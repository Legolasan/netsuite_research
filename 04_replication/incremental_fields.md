# NetSuite Incremental Sync Fields Reference

This document lists all fields that can be used for incremental synchronization.

## 1. Standard Incremental Fields

### 1.1 lastModifiedDate

The primary field used for incremental sync. Available on most record types.

| Search Class | Field | Data Type |
|--------------|-------|-----------|
| TransactionSearchBasic | lastModifiedDate | SearchDateField |
| ItemSearchBasic | lastModifiedDate | SearchDateField |
| CustomerSearchBasic | lastModifiedDate | SearchDateField |
| VendorSearchBasic | lastModifiedDate | SearchDateField |
| EmployeeSearchBasic | lastModifiedDate | SearchDateField |
| ContactSearchBasic | lastModifiedDate | SearchDateField |
| PartnerSearchBasic | lastModifiedDate | SearchDateField |

### 1.2 dateCreated

Useful for initial historical loads.

| Search Class | Field | Data Type |
|--------------|-------|-----------|
| TransactionSearchBasic | dateCreated | SearchDateField |
| CustomerSearchBasic | dateCreated | SearchDateField |
| VendorSearchBasic | dateCreated | SearchDateField |

### 1.3 deletedDate

Used specifically for tracking deleted records.

| API | Field | Data Type |
|-----|-------|-----------|
| getDeleted | deletedDate | DateTime |

---

## 2. Transaction-Specific Fields

### 2.1 Common Transaction Fields

| Field | Description | Use Case |
|-------|-------------|----------|
| lastModifiedDate | Last modification timestamp | Incremental sync |
| dateCreated | Record creation date | Historical load |
| tranDate | Transaction date | Business date filtering |
| postingPeriod | Accounting period | Period-based sync |

### 2.2 Status-Based Fields

Some transactions support status-based filtering:

| Field | Transaction Types |
|-------|-------------------|
| status | All transactions |
| orderStatus | SalesOrder, PurchaseOrder |
| paymentStatus | Payments |

---

## 3. Entity-Specific Fields

### 3.1 Customer Fields

| Field | Type | Incremental Use |
|-------|------|-----------------|
| lastModifiedDate | DateTime | Primary incremental |
| dateCreated | DateTime | Historical load |
| lastSaleDate | DateTime | Sales activity tracking |

### 3.2 Vendor Fields

| Field | Type | Incremental Use |
|-------|------|-----------------|
| lastModifiedDate | DateTime | Primary incremental |
| dateCreated | DateTime | Historical load |

### 3.3 Employee Fields

| Field | Type | Incremental Use |
|-------|------|-----------------|
| lastModifiedDate | DateTime | Primary incremental |
| dateCreated | DateTime | Historical load |
| hireDate | Date | HR tracking |
| releaseDate | Date | Termination tracking |

---

## 4. Item-Specific Fields

| Field | Type | Description |
|-------|------|-------------|
| lastModifiedDate | DateTime | Primary incremental field |
| dateCreated | DateTime | Item creation date |
| lastPurchasePrice | Currency | Price tracking |

---

## 5. Search Filter Operators

### 5.1 Date Operators

| Operator | Use Case |
|----------|----------|
| ON_OR_AFTER | Incremental from date |
| AFTER | Exclusive from date |
| BEFORE | Up to date |
| BETWEEN | Date range |
| IS_EMPTY | Null dates |
| IS_NOT_EMPTY | Non-null dates |

### 5.2 Example Usage

```java
// Incremental search filter
SearchDateField lastModified = new SearchDateField();
lastModified.setOperator(SearchDateFieldOperator.ON_OR_AFTER);
lastModified.setSearchValue(
    DatatypeFactory.newInstance()
        .newXMLGregorianCalendar("2026-01-15T00:00:00Z")
);
searchBasic.setLastModifiedDate(lastModified);
```

---

## 6. Objects Without Incremental Support

These objects don't have lastModifiedDate in their SearchBasic:

| Object | Reason | Alternative |
|--------|--------|-------------|
| Account | No modification tracking | Full load |
| Department | No modification tracking | Full load |
| Location | No modification tracking | Full load |
| Subsidiary | No modification tracking | Full load |
| Term | Reference data | Full load |
| TaxCode | Reference data | Full load |

---

## 7. Incremental Field Matrix

### Currently Incremental (in Connector)

| Category | Field | Status |
|----------|-------|--------|
| Transaction | lastModifiedDate | ✅ Active |
| Item | lastModifiedDate | ✅ Active |
| Delete | deletedDate | ✅ Active |

### Available but Not Used (Full Load in Connector)

| Object | Field Available | Status |
|--------|-----------------|--------|
| Customer | lastModifiedDate | ⚠️ Not used |
| Vendor | lastModifiedDate | ⚠️ Not used |
| Contact | lastModifiedDate | ⚠️ Not used |
| Employee | lastModifiedDate | ⚠️ Not used |
| Partner | lastModifiedDate | ⚠️ Not used |
| SupportCase | lastModifiedDate | ⚠️ Not used |
| Issue | lastModifiedDate | ⚠️ Not used |
| Message | lastModifiedDate | ⚠️ Not used |
| Note | lastModifiedDate | ⚠️ Not used |
| File | lastModifiedDate | ⚠️ Not used |
| PhoneCall | lastModifiedDate | ⚠️ Not used |
| CalendarEvent | lastModifiedDate | ⚠️ Not used |
| TimeBill | lastModifiedDate | ⚠️ Not used |
| TimeEntry | lastModifiedDate | ⚠️ Not used |
| Paycheck | lastModifiedDate | ⚠️ Not used |
| Solution | lastModifiedDate | ⚠️ Not used |
| GiftCertificate | lastModifiedDate | ⚠️ Not used |

---

## 8. REST API Incremental Fields

For REST API (future enhancement):

| Field | Endpoint | Description |
|-------|----------|-------------|
| lastmodifieddate | All records | Standard modification date |
| datecreated | All records | Creation date |

### REST Query Example

```
GET /services/rest/record/v1/customer
?q=lastmodifieddate AFTER "2026-01-15T00:00:00Z"
&limit=1000
&offset=0
```

---

## 9. SuiteQL Date Fields

For SuiteQL queries (future enhancement):

```sql
-- Transaction incremental query
SELECT *
FROM transaction
WHERE lastmodifieddate >= TO_TIMESTAMP('2026-01-15 00:00:00', 'YYYY-MM-DD HH24:MI:SS')
ORDER BY lastmodifieddate ASC

-- Customer incremental query
SELECT *
FROM customer
WHERE lastmodifieddate >= TO_TIMESTAMP('2026-01-15 00:00:00', 'YYYY-MM-DD HH24:MI:SS')
ORDER BY lastmodifieddate ASC
```
