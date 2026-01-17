"""
AUDIT
Audit logging and historical tracking
Part of the modularized YuKyuDATA database layer
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

from database import get_db, USE_POSTGRESQL, _convert_query_placeholders
from services.crypto_utils import encrypt_field, decrypt_field, get_encryption_manager

# ============================================

def log_audit(
    action: str,
    entity_type: str,
    entity_id: str = None,
    old_value: Any = None,
    new_value: Any = None,
    user_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    additional_info: Dict = None
) -> int:
    """
    Registra una accion en el audit log.

    Args:
        action: Tipo de accion (CREATE, UPDATE, DELETE, APPROVE, REJECT, REVERT, LOGIN, etc.)
        entity_type: Tipo de entidad (employee, leave_request, yukyu_usage, genzai, ukeoi, etc.)
        entity_id: ID de la entidad afectada
        old_value: Valor anterior (dict o cualquier valor serializable a JSON)
        new_value: Nuevo valor (dict o cualquier valor serializable a JSON)
        user_id: ID del usuario que realizo la accion
        ip_address: Direccion IP del cliente
        user_agent: User-Agent del navegador
        additional_info: Informacion adicional (dict)

    Returns:
        ID del registro de audit creado
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Serializar valores a JSON si son diccionarios o listas
        old_value_json = json.dumps(old_value, ensure_ascii=False, default=str) if old_value is not None else None
        new_value_json = json.dumps(new_value, ensure_ascii=False, default=str) if new_value is not None else None
        additional_info_json = json.dumps(additional_info, ensure_ascii=False, default=str) if additional_info else None

        if USE_POSTGRESQL:
            c.execute('''
                INSERT INTO audit_log
                (timestamp, user_id, action, entity_type, entity_id, old_value, new_value, ip_address, user_agent, additional_info)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (timestamp, user_id, action, entity_type, entity_id, old_value_json, new_value_json, ip_address, user_agent, additional_info_json))
            audit_id = c.fetchone()[0]
        else:
            c.execute('''
                INSERT INTO audit_log
                (timestamp, user_id, action, entity_type, entity_id, old_value, new_value, ip_address, user_agent, additional_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, user_id, action, entity_type, entity_id, old_value_json, new_value_json, ip_address, user_agent, additional_info_json))
            audit_id = c.lastrowid

        conn.commit()
        return audit_id


def get_audit_log(
    entity_type: str = None,
    entity_id: str = None,
    action: str = None,
    user_id: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Obtiene registros del audit log con filtros opcionales.

    Args:
        entity_type: Filtrar por tipo de entidad
        entity_id: Filtrar por ID de entidad
        action: Filtrar por tipo de accion
        user_id: Filtrar por usuario
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)
        limit: Maximo de registros a retornar
        offset: Offset para paginacion

    Returns:
        Lista de registros de audit
    """
    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)

        if action:
            query += " AND action = ?"
            params.append(action)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date + "T23:59:59")

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = c.execute(query, tuple(params)).fetchall()

        # Parsear JSON en old_value y new_value
        result = []
        for row in rows:
            record = dict(row)
            if record.get('old_value'):
                try:
                    record['old_value'] = json.loads(record['old_value'])
                except (json.JSONDecodeError, TypeError):
                    pass
            if record.get('new_value'):
                try:
                    record['new_value'] = json.loads(record['new_value'])
                except (json.JSONDecodeError, TypeError):
                    pass
            if record.get('additional_info'):
                try:
                    record['additional_info'] = json.loads(record['additional_info'])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(record)

        return result


def get_audit_log_by_user(user_id: str, limit: int = 100) -> List[Dict]:
    """
    Obtiene todos los registros de audit de un usuario especifico.

    Args:
        user_id: ID del usuario
        limit: Maximo de registros a retornar

    Returns:
        Lista de registros de audit del usuario
    """
    return get_audit_log(user_id=user_id, limit=limit)


def get_entity_history(entity_type: str, entity_id: str, limit: int = 50) -> List[Dict]:
    """
    Obtiene el historial completo de cambios de una entidad.

    Args:
        entity_type: Tipo de entidad
        entity_id: ID de la entidad
        limit: Maximo de registros

    Returns:
        Lista de cambios ordenados por fecha (mas reciente primero)
    """
    return get_audit_log(entity_type=entity_type, entity_id=entity_id, limit=limit)


def get_audit_stats(days: int = 30) -> Dict:
    """
    Obtiene estadisticas del audit log.

    Args:
        days: Numero de dias hacia atras para calcular estadisticas

    Returns:
        Dict con estadisticas de auditoría
    """
    with get_db() as conn:
        c = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Conteo por tipo de accion
        actions_query = """
            SELECT action, COUNT(*) as count
            FROM audit_log
            WHERE timestamp >= ?
            GROUP BY action
            ORDER BY count DESC
        """
        action_rows = c.execute(actions_query, (cutoff_date,)).fetchall()
        actions = {row['action']: row['count'] for row in action_rows}

        # Conteo por tipo de entidad
        entities_query = """
            SELECT entity_type, COUNT(*) as count
            FROM audit_log
            WHERE timestamp >= ?
            GROUP BY entity_type
            ORDER BY count DESC
        """
        entity_rows = c.execute(entities_query, (cutoff_date,)).fetchall()
        entities = {row['entity_type']: row['count'] for row in entity_rows}

        # Conteo por usuario
        users_query = """
            SELECT user_id, COUNT(*) as count
            FROM audit_log
            WHERE timestamp >= ? AND user_id IS NOT NULL
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 10
        """
        user_rows = c.execute(users_query, (cutoff_date,)).fetchall()
        top_users = {row['user_id']: row['count'] for row in user_rows}

        # Total de registros
        total = c.execute(
            "SELECT COUNT(*) as total FROM audit_log WHERE timestamp >= ?",
            (cutoff_date,)
        ).fetchone()['total']

        return {
            "period_days": days,
            "total_records": total,
            "by_action": actions,
            "by_entity_type": entities,
            "top_users": top_users
        }
