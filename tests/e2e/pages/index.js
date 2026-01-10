/**
 * Page Objects Index
 * Exporta todos los Page Objects para uso en tests
 */

const { BasePage } = require('./BasePage');
const { DashboardPage } = require('./DashboardPage');
const { EditYukyuPage } = require('./EditYukyuPage');
const { BulkEditPage } = require('./BulkEditPage');
const { LeaveRequestPage } = require('./LeaveRequestPage');

module.exports = {
  BasePage,
  DashboardPage,
  EditYukyuPage,
  BulkEditPage,
  LeaveRequestPage,
};
