# NetSuite Permissions Reference

This document details the permission requirements for accessing NetSuite objects via SOAP and REST Web Services.

## 1. Overview

NetSuite uses a role-based permission system. To access records via APIs, you need:

1. **Web Services Access** - Permission to use SOAP/REST APIs
2. **Record-Level Permissions** - View, Create, Edit, or Full access per record type
3. **Role Assignment** - User must have an appropriate role

---

## 2. Required Base Permissions

### 2.1 Web Services Access

| Permission | Location | Required |
|------------|----------|----------|
| Web Services | Setup > Users/Roles > Access | Yes |
| SOAP Web Services | Setup > Integration | Yes |
| REST Web Services | Setup > Integration | For REST |
| Log in using Access Tokens | Setup > Users/Roles | For Token-Based Auth |

### 2.2 Setup Permissions

| Permission | Description |
|------------|-------------|
| Custom Record Types | Access custom records |
| Custom Fields | Access custom field definitions |
| Custom Lists | Access custom lists |
| Saved Searches | Access saved searches |

---

## 3. Record Type Permissions

### 3.1 Transaction Records

| Record Type | Permission Name | View | Create | Edit | Full |
|-------------|-----------------|------|--------|------|------|
| Invoice | Transactions > Invoice | R | R | R | RW |
| Sales Order | Transactions > Sales Order | R | R | R | RW |
| Purchase Order | Transactions > Purchase Order | R | R | R | RW |
| Cash Sale | Transactions > Cash Sale | R | R | R | RW |
| Credit Memo | Transactions > Credit Memo | R | R | R | RW |
| Customer Payment | Transactions > Customer Payment | R | R | R | RW |
| Vendor Bill | Transactions > Vendor Bill | R | R | R | RW |
| Vendor Payment | Transactions > Vendor Payment | R | R | R | RW |
| Journal Entry | Transactions > Make Journal Entry | R | R | R | RW |
| Estimate | Transactions > Estimate | R | R | R | RW |
| Item Fulfillment | Transactions > Item Fulfillment | R | R | R | RW |
| Item Receipt | Transactions > Item Receipt | R | R | R | RW |
| Return Authorization | Transactions > Return Authorization | R | R | R | RW |
| Work Order | Transactions > Work Order | R | R | R | RW |
| Transfer Order | Transactions > Transfer Order | R | R | R | RW |
| Inventory Adjustment | Transactions > Inventory Adjustment | R | R | R | RW |
| Deposit | Transactions > Deposit | R | R | R | RW |
| Check | Transactions > Check | R | R | R | RW |

*R = Read access, RW = Read/Write access*

### 3.2 Entity Records

| Record Type | Permission Name | View | Create | Edit | Full |
|-------------|-----------------|------|--------|------|------|
| Customer | Lists > Customers | R | R | R | RW |
| Vendor | Lists > Vendors | R | R | R | RW |
| Employee | Lists > Employees | R | R | R | RW |
| Contact | Lists > Contacts | R | R | R | RW |
| Partner | Lists > Partners | R | R | R | RW |
| Job/Project | Lists > Jobs | R | R | R | RW |

### 3.3 Item Records

| Record Type | Permission Name | View | Create | Edit | Full |
|-------------|-----------------|------|--------|------|------|
| Inventory Item | Lists > Items | R | R | R | RW |
| Assembly Item | Lists > Items | R | R | R | RW |
| Non-Inventory Item | Lists > Items | R | R | R | RW |
| Service Item | Lists > Items | R | R | R | RW |
| Kit Item | Lists > Items | R | R | R | RW |
| Other Charge Item | Lists > Items | R | R | R | RW |

### 3.4 Setup/Reference Records

| Record Type | Permission Name | Minimum Level |
|-------------|-----------------|---------------|
| Account | Lists > Accounts | View |
| Department | Lists > Departments | View |
| Location | Lists > Locations | View |
| Subsidiary | Lists > Subsidiaries | View |
| Classification | Lists > Classes | View |
| Currency | Lists > Currencies | View |
| Terms | Lists > Terms | View |
| Tax Codes | Lists > Tax Codes | View |
| Price Level | Lists > Price Levels | View |
| Sales Role | Lists > Sales Role | View |

---

## 4. Permission Levels

| Level | Description | API Operations |
|-------|-------------|----------------|
| **None** | No access | - |
| **View** | Read-only access | search, get, getList |
| **Create** | Can create new records | add, search, get |
| **Edit** | Can modify existing records | update, search, get |
| **Full** | Complete access | add, update, delete, search, get |

---

## 5. Special Permissions

### 5.1 Delete Permissions

To track deleted records via `getDeleted` operation:

| Permission | Location |
|------------|----------|
| Deleted Records | Setup > View Deleted Records |

### 5.2 Custom Record Permissions

For each custom record type, permissions are set individually:

| Permission | Description |
|------------|-------------|
| Custom Record Type | Access to specific custom record |
| Custom Record Entries | Access to instances of that type |

### 5.3 Advanced Permissions

| Permission | Use Case |
|------------|----------|
| SuiteScript | Required for some advanced operations |
| SuiteAnalytics Workbook | Access to workbook data |
| Export Lists | Bulk data export |
| Import CSV Records | Bulk import |

---

## 6. Role Recommendations

### 6.1 Read-Only Integration Role

For ETL/data extraction purposes:

```
Recommended Permissions:
- Web Services: Yes
- Transactions: View level for all needed types
- Lists: View level for all entities and items
- Setup: View level for reference data
- Custom Record Types: View level
- Deleted Records: View
```

### 6.2 Full Integration Role

For bidirectional sync:

```
Recommended Permissions:
- Web Services: Yes
- Transactions: Full level
- Lists: Full level
- Setup: Edit level
- Custom Record Types: Full level
- Deleted Records: View
```

---

## 7. Subsidiary Restrictions

In OneWorld accounts:

| Setting | Impact |
|---------|--------|
| Restrict to Subsidiary | Role can only access records in assigned subsidiaries |
| Include Children | Access includes child subsidiaries |
| Cross-Subsidiary | Access across all subsidiaries |

---

## 8. API-Specific Considerations

### 8.1 SOAP Web Services

- Requires "Web Services" permission
- Operations respect record-level permissions
- Search operations require View or higher

### 8.2 REST Web Services

- Requires "REST Web Services" permission
- Same record-level permissions as SOAP
- Additional "RESTlet" permission for custom endpoints

### 8.3 SuiteQL

- Requires "SuiteAnalytics Workbook" or "Report" permissions
- Query access follows record permissions

---

## 9. Permission Check Methods

### 9.1 Via SOAP

```xml
<!-- Check permissions using getSelectValue -->
<getSelectValue>
  <field>recordType</field>
  <customRecordType>...</customRecordType>
</getSelectValue>
```

### 9.2 Via Role Customization

1. Navigate to Setup > Users/Roles > Manage Roles
2. Edit the integration role
3. Review Permissions tab
4. Set appropriate levels for each record type

---

## 10. Common Permission Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `INSUFFICIENT_PERMISSION` | Missing record permission | Grant appropriate level |
| `USER_ERROR` | User cannot access record | Check role assignment |
| `INVALID_ROLE` | Role lacks web services | Enable web services |
| `SSS_MISSING_REQD_ARGUMENT` | Missing required permission | Review role permissions |

---

## 11. Connector Required Permissions Summary

For the current ETL connector implementation:

| Category | Minimum Permission |
|----------|-------------------|
| All Transactions | View |
| All Entities | View |
| All Items | View |
| Setup Records | View |
| Custom Records | View |
| Deleted Records | View |
| Web Services | Enabled |
