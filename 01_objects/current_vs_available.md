# NetSuite Objects: Current Implementation vs. Available

This document compares what's currently implemented in the connector against what NetSuite offers.

## Implementation Summary

| Aspect | Current | Available | Gap |
|--------|---------|-----------|-----|
| API Protocol | SOAP only | SOAP + REST | REST not implemented |
| SDK Version | v2022_1 | v2024_1+ | 2 versions behind |
| Transaction Types | 37 | 40+ | ~3 types missing |
| Item Types | 24 | 26+ | ~2 types missing |
| Standard Objects | 67 | 100+ | ~33+ objects missing |
| Incremental Sync | Transaction, Item, Delete | 17+ additional | Major opportunity |

---

## 1. Transaction Objects

### Currently Implemented (37)
All major transaction types are implemented with incremental sync support.

### Not Implemented / Available in NetSuite

| Object | API Support | Priority | Notes |
|--------|-------------|----------|-------|
| AdvInterCompanyJournalEntry | SOAP/REST | Medium | Advanced intercompany |
| Blanket Purchase Order | REST | Low | REST-only record |
| Revenue Arrangement | REST | Medium | ASC 606 compliance |
| Revenue Plan | REST | Medium | Revenue recognition |

---

## 2. Item Objects

### Currently Implemented (24)
All common item types are implemented.

### Not Implemented / Available in NetSuite

| Object | API Support | Priority | Notes |
|--------|-------------|----------|-------|
| Supply Chain Snapshot | REST | Low | Supply chain module |
| Manufacturing Cost Template | REST | Low | Manufacturing |

---

## 3. Entity Objects

### Improvement Opportunities

These objects are implemented as **Full Load** but support **Incremental Sync**:

| Object | Current Mode | Potential Mode | Impact |
|--------|--------------|----------------|--------|
| **Customer** | Full Load | Incremental | High - Large datasets |
| **Vendor** | Full Load | Incremental | High - Large datasets |
| **Employee** | Full Load | Incremental | Medium |
| **Contact** | Full Load | Incremental | High - Often large |
| **Partner** | Full Load | Incremental | Medium |

### Recommended Priority for Incremental Conversion

1. **High Priority** (Large datasets, frequent changes):
   - Customer
   - Vendor
   - Contact

2. **Medium Priority**:
   - Employee
   - Partner
   - SupportCase
   - Issue

3. **Lower Priority** (Smaller datasets):
   - CalendarEvent
   - PhoneCall
   - Message
   - Note

---

## 4. REST API Objects (Not Implemented)

NetSuite REST API offers additional objects not available via SOAP:

### REST-Only Records

| Object | Description | Priority |
|--------|-------------|----------|
| Revenue Arrangement | ASC 606 revenue | High |
| Revenue Plan | Revenue schedules | High |
| Revenue Element | Revenue recognition | Medium |
| Commerce Category | E-commerce | Low |
| Store Tab | E-commerce | Low |
| Blanket Purchase Order | Procurement | Medium |
| Purchase Contract | Procurement | Medium |
| Subscription | SuiteBilling | Medium |
| Subscription Line | SuiteBilling | Medium |
| Subscription Plan | SuiteBilling | Medium |
| Usage | SuiteBilling | Low |
| Billing Account | SuiteBilling | Medium |

---

## 5. Search/Query Capabilities

### Current Implementation
- Basic Search
- Saved Search
- Advanced Search (SOAP)

### Available but Not Implemented

| Capability | Description | Priority |
|------------|-------------|----------|
| **SuiteQL** | SQL-like query language | High |
| REST Query | RESTlet-based queries | Medium |
| Workbook Analytics | Workbook data access | Low |

### SuiteQL Benefits
- More flexible queries
- Better performance for complex filters
- Join capabilities
- Aggregation support

---

## 6. API Features Comparison

| Feature | SOAP (Current) | REST (Available) |
|---------|---------------|------------------|
| Record CRUD | Yes | Yes |
| Search | Basic, Saved, Advanced | SuiteQL, Query |
| Bulk Operations | Limited | Yes (asyncAddList) |
| Sublist Access | Yes | Yes |
| Custom Fields | Yes | Yes |
| File Upload | Yes | Yes (chunked) |
| Async Operations | No | Yes |
| Rate Limits | By governance | By governance |

---

## 7. Improvement Roadmap

### Phase 1: Quick Wins (Low Effort, High Impact)
1. Enable incremental sync for Customer, Vendor, Contact
2. Add missing transaction types
3. Upgrade SDK to latest version

### Phase 2: REST API Integration (Medium Effort)
1. Add REST API client alongside SOAP
2. Implement SuiteQL query support
3. Add REST-only objects (Revenue, Subscription)

### Phase 3: Advanced Features (Higher Effort)
1. Async bulk operations
2. Write operations (add, update, delete)
3. Transform operations (Quote to Order)

---

## 8. Object Coverage Matrix

```
Legend: 
  [x] Implemented
  [~] Implemented (Full Load, could be Incremental)
  [ ] Not Implemented

TRANSACTIONS
[x] Invoice           [x] SalesOrder        [x] PurchaseOrder
[x] CashSale          [x] CreditMemo        [x] VendorBill
[x] JournalEntry      [x] Check             [x] Deposit
[x] CustomerPayment   [x] VendorPayment     [x] TransferOrder
[x] WorkOrder         [x] ItemFulfillment   [x] ItemReceipt
... (37 total implemented)

ITEMS
[x] InventoryItem     [x] AssemblyItem      [x] KitItem
[x] ServiceItem       [x] NonInventoryItem  [x] DownloadItem
... (24 total implemented)

ENTITIES
[~] Customer          [~] Vendor            [~] Employee
[~] Contact           [~] Partner           [x] Job
... (could be incremental)

SETUP/REFERENCE
[x] Account           [x] Department        [x] Location
[x] Subsidiary        [x] Classification    [x] Currency
... (67 total)

CUSTOM
[x] CustomRecord      [x] CustomTransaction [x] CustomList

REST-ONLY (NOT IMPLEMENTED)
[ ] RevenueArrangement    [ ] RevenuePlan
[ ] Subscription          [ ] BlanketPurchaseOrder
```

---

## Source References

- Current Implementation: `Connector_Code/erp/connector/record/`
- NetSuite SOAP Records: SDK `platform/core/types/RecordType.java`
- NetSuite REST Records: PDF Documentation
