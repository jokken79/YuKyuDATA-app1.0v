/**
 * Image Optimizer Module
 * Optimiza y comprime imágenes automáticamente
 * @module image-optimizer
 */

/**
 * Clase para optimizar imágenes
 */
export class ImageOptimizer {
    constructor(options = {}) {
        /** @type {number} Calidad por defecto (0.8) */
        this.defaultQuality = options.quality || 0.8;
        
        /** @type {number} Ancho máximo por defecto (1920px) */
        this.maxWidth = options.maxWidth || 1920;
        
        /** @type {number} Alto máximo por defecto (1080px) */
        this.maxHeight = options.maxHeight || 1080;
        
        /** @type {Array} Formatos soportados */
        this.supportedFormats = ['image/jpeg', 'image/png', 'image/webp'];
        
        /** @type {Map} Cache de imágenes optimizadas */
        this.cache = new Map();
        
        /** @type {boolean} Usar WebP si está disponible */
        this.useWebP = this._supportsWebP();
    }

    /**
     * Verifica si el navegador soporta WebP
     * @returns {boolean} - True si soporta WebP
     * @private
     */
    _supportsWebP() {
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        
        return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    }

    /**
     * Carga una imagen desde una URL
     * @param {string} url - URL de la imagen
     * @returns {Promise<HTMLImageElement>} - Promesa con la imagen cargada
     * @private
     */
    _loadImage(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            
            img.onload = () => resolve(img);
            img.onerror = () => reject(new Error(`Failed to load image: ${url}`));
            
            img.src = url;
        });
    }

    /**
     * Calcula las dimensiones optimizadas manteniendo aspect ratio
     * @param {number} originalWidth - Ancho original
     * @param {number} originalHeight - Alto original
     * @returns {Object} - Dimensiones optimizadas
     * @private
     */
    _calculateOptimizedDimensions(originalWidth, originalHeight) {
        let { width, height } = { width: originalWidth, height: originalHeight };
        
        // Reducir si excede las dimensiones máximas
        if (width > this.maxWidth || height > this.maxHeight) {
            const aspectRatio = width / height;
            
            if (width > this.maxWidth) {
                width = this.maxWidth;
                height = width / aspectRatio;
            }
            
            if (height > this.maxHeight) {
                height = this.maxHeight;
                width = height * aspectRatio;
            }
        }
        
        return { width: Math.round(width), height: Math.round(height) };
    }

    /**
     * Optimiza una imagen usando canvas
     * @param {HTMLImageElement} img - Imagen a optimizar
     * @param {Object} options - Opciones de optimización
     * @returns {Promise<Blob>} - Promesa con la imagen optimizada
     * @private
     */
    _optimizeImage(img, options = {}) {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Calcular dimensiones optimizadas
            const { width, height } = this._calculateOptimizedDimensions(
                img.naturalWidth, 
                img.naturalHeight
            );
            
            canvas.width = width;
            canvas.height = height;
            
            // Dibujar imagen optimizada
            ctx.drawImage(img, 0, 0, width, height);
            
            // Determinar formato de salida
            const format = options.format || (this.useWebP ? 'image/webp' : 'image/jpeg');
            const quality = options.quality || this.defaultQuality;
            
            // Convertir a blob
            canvas.toBlob(resolve, format, quality);
        });
    }

    /**
     * Optimiza una imagen desde una URL
     * @param {string} url - URL de la imagen
     * @param {Object} options - Opciones de optimización
     * @returns {Promise<Blob>} - Promesa con la imagen optimizada
     */
    async optimizeFromUrl(url, options = {}) {
        // Verificar cache primero
        const cacheKey = `${url}_${JSON.stringify(options)}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }
        
        try {
            // Cargar imagen original
            const img = await this._loadImage(url);
            
            // Optimizar imagen
            const optimizedBlob = await this._optimizeImage(img, options);
            
            // Guardar en cache
            this.cache.set(cacheKey, optimizedBlob);
            
            return optimizedBlob;
        } catch (error) {
            console.error('Image optimization failed:', error);
            throw error;
        }
    }

    /**
     * Optimiza una imagen desde un archivo
     * @param {File} file - Archivo de imagen
     * @param {Object} options - Opciones de optimización
     * @returns {Promise<Blob>} - Promesa con la imagen optimizada
     */
    async optimizeFromFile(file, options = {}) {
        try {
            // Verificar formato soportado
            if (!this.supportedFormats.includes(file.type)) {
                throw new Error(`Unsupported format: ${file.type}`);
            }
            
            // Crear URL temporal y cargar imagen
            const url = URL.createObjectURL(file);
            const img = await this._loadImage(url);
            URL.revokeObjectURL(url);
            
            // Optimizar imagen
            const optimizedBlob = await this._optimizeImage(img, {
                ...options,
                format: file.type
            });
            
            return optimizedBlob;
        } catch (error) {
            console.error('File optimization failed:', error);
            throw error;
        }
    }

    /**
     * Convierte una imagen optimizada a File
     * @param {Blob} blob - Blob optimizado
     * @param {string} filename - Nombre del archivo
     * @returns {File} - Archivo optimizado
     */
    blobToFile(blob, filename) {
        const extension = blob.type.split('/')[1];
        const name = filename.replace(/\.[^/.]+$/, '') + `_optimized.${extension}`;
        
        return new File([blob], name, { type: blob.type });
    }

    /**
     * Genera múltiples tamaños de una imagen
     * @param {string|File} source - Fuente de la imagen
     * @param {Array<Object>} sizes - Array de tamaños deseados
     * @returns {Promise<Array>} - Promesa con las imágenes generadas
     */
    async generateResponsiveImages(source, sizes = [
        { name: 'small', width: 320 },
        { name: 'medium', width: 768 },
        { name: 'large', width: 1024 }
    ]) {
        try {
            let img;
            
            if (typeof source === 'string') {
                img = await this._loadImage(source);
            } else if (source instanceof File) {
                const url = URL.createObjectURL(source);
                img = await this._loadImage(url);
                URL.revokeObjectURL(url);
            } else {
                throw new Error('Invalid source type');
            }
            
            const responsiveImages = [];
            
            for (const size of sizes) {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // Calcular altura manteniendo aspect ratio
                const aspectRatio = img.naturalWidth / img.naturalHeight;
                const height = size.width / aspectRatio;
                
                canvas.width = size.width;
                canvas.height = height;
                
                // Dibujar imagen redimensionada
                ctx.drawImage(img, 0, 0, size.width, height);
                
                // Generar blob
                const blob = await new Promise(resolve => {
                    canvas.toBlob(resolve, this.useWebP ? 'image/webp' : 'image/jpeg', 0.8);
                });
                
                responsiveImages.push({
                    name: size.name,
                    width: size.width,
                    height: Math.round(height),
                    blob: blob,
                    url: URL.createObjectURL(blob)
                });
            }
            
            return responsiveImages;
        } catch (error) {
            console.error('Responsive images generation failed:', error);
            throw error;
        }
    }

    /**
     * Limpia el cache de imágenes
     */
    clearCache() {
        // Revocar URLs de objetos
        for (const [key, blob] of this.cache.entries()) {
            if (typeof blob === 'object' && blob.url) {
                URL.revokeObjectURL(blob.url);
            }
        }
        
        this.cache.clear();
    }

    /**
     * Obtiene estadísticas de optimización
     * @returns {Object} - Estadísticas
     */
    getStats() {
        return {
            cacheSize: this.cache.size,
            supportedFormats: this.supportedFormats,
            useWebP: this.useWebP,
            maxWidth: this.maxWidth,
            maxHeight: this.maxHeight,
            defaultQuality: this.defaultQuality
        };
    }

    /**
     * Comprime una imagen usando canvas y filtros
     * @param {HTMLImageElement} img - Imagen a comprimir
     * @param {number} quality - Calidad de compresión (0-1)
     * @returns {Promise<Blob>} - Promesa con la imagen comprimida
     */
    async compressImage(img, quality = 0.7) {
        return new Promise((resolve) => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            
            // Aplicar filtros de compresión
            ctx.filter = 'contrast(1.1) saturate(1.1)';
            ctx.drawImage(img, 0, 0);
            
            canvas.toBlob(resolve, 'image/jpeg', quality);
        });
    }

    /**
     * Crea un placeholder de imagen optimizado
     * @param {number} width - Ancho del placeholder
     * @param {number} height - Alto del placeholder
     * @param {string} color - Color del placeholder
     * @returns {string} - URL del placeholder
     */
    createPlaceholder(width, height, color = '#e5e7eb') {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = width;
        canvas.height = height;
        
        // Rellenar con color
        ctx.fillStyle = color;
        ctx.fillRect(0, 0, width, height);
        
        // Añadir texto opcional
        ctx.fillStyle = '#6b7280';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${width}×${height}`, width / 2, height / 2);
        
        return canvas.toDataURL('image/png');
    }
}

/**
 * Lazy Loading de imágenes
 */
export class ImageLazyLoader {
    constructor(options = {}) {
        /** @type {number} Margen de carga (px) */
        this.margin = options.margin || 100;
        
        /** @type {number} Tiempo de debounce (ms) */
        this.debounceTime = options.debounceTime || 100;
        
        /** @type {Map} Imágenes observadas */
        this.observedImages = new Map();
        
        /** @type {IntersectionObserver} Observer */
        this.observer = null;
        
        this._setupObserver();
        this._setupScrollListener();
    }

    /**
     * Configura el Intersection Observer
     * @private
     */
    _setupObserver() {
        this.observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this._loadImage(entry.target);
                        this.observer.unobserve(entry.target);
                    }
                });
            },
            {
                rootMargin: `${this.margin}px`,
                threshold: 0.1
            }
        );
    }

    /**
     * Configura el listener de scroll con debounce
     * @private
     */
    _setupScrollListener() {
        let timeoutId;
        
        const handleScroll = () => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                this._checkImages();
            }, this.debounceTime);
        };
        
        window.addEventListener('scroll', handleScroll, { passive: true });
        window.addEventListener('resize', handleScroll, { passive: true });
    }

    /**
     * Observa una imagen para lazy loading
     * @param {HTMLImageElement} img - Imagen a observar
     */
    observe(img) {
        if (!img.dataset.src) {
            img.dataset.src = img.src;
        }
        
        // Establecer placeholder
        if (!img.src) {
            const width = img.width || 300;
            const height = img.height || 200;
            img.src = this._createPlaceholder(width, height);
        }
        
        this.observedImages.set(img, true);
        this.observer.observe(img);
    }

    /**
     * Carga una imagen
     * @param {HTMLImageElement} img - Imagen a cargar
     * @private
     */
    _loadImage(img) {
        const src = img.dataset.src;
        
        if (src && !img.src.includes('placeholder')) {
            img.src = src;
            img.classList.add('loaded');
        }
        
        this.observedImages.delete(img);
    }

    /**
     * Verifica imágenes manualmente
     * @private
     */
    _checkImages() {
        this.observedImages.forEach((_, img) => {
            const rect = img.getBoundingClientRect();
            const isInViewport = (
                rect.top >= -this.margin &&
                rect.left >= -this.margin &&
                rect.bottom <= window.innerHeight + this.margin &&
                rect.right <= window.innerWidth + this.margin
            );
            
            if (isInViewport) {
                this._loadImage(img);
                this.observer.unobserve(img);
            }
        });
    }

    /**
     * Crea un placeholder simple
     * @param {number} width - Ancho
     * @param {number} height - Alto
     * @returns {string} - Data URL del placeholder
     * @private
     */
    _createPlaceholder(width, height) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = width;
        canvas.height = height;
        
        ctx.fillStyle = '#f3f4f6';
        ctx.fillRect(0, 0, width, height);
        
        return canvas.toDataURL('image/png');
    }

    /**
     * Destruye el lazy loader
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        
        this.observedImages.clear();
        
        window.removeEventListener('scroll', this._handleScroll);
        window.removeEventListener('resize', this._handleScroll);
    }
}

/**
 * Instancias globales
 */
export const imageOptimizer = new ImageOptimizer();
export const lazyLoader = new ImageLazyLoader();

/**
 * Función de conveniencia para optimizar imágenes automáticamente
 * @param {NodeList|Array} images - Imágenes a optimizar
 * @param {Object} options - Opciones de optimización
 */
export async function optimizeImages(images, options = {}) {
    const promises = Array.from(images).map(async (img) => {
        try {
            if (img.dataset.optimized !== 'true') {
                const optimizedBlob = await imageOptimizer.optimizeFromUrl(img.src, options);
                const optimizedUrl = URL.createObjectURL(optimizedBlob);
                
                img.src = optimizedUrl;
                img.dataset.optimized = 'true';
                img.dataset.originalSrc = img.src;
                
                // Cleanup cuando la imagen se carga
                img.onload = () => {
                    URL.revokeObjectURL(optimizedUrl);
                };
            }
        } catch (error) {
            console.warn('Failed to optimize image:', img.src, error);
        }
    });
    
    await Promise.allSettled(promises);
}

export default ImageOptimizer;