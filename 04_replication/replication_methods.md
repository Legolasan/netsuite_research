# NetSuite Replication Methods

This document details the replication strategies supported by the connector and potential improvements.

## 1. Current Implementation Overview

| Method | Objects | Mechanism | Offset Field |
|--------|---------|-----------|--------------|
| **Incremental** | Transaction, Item | lastModifiedDate filter | lastModifiedDate |
| **Full Load** | Standard Records (67) | Complete refresh | None |
| **Delete Tracking** | All supported | getDeleted API | deletedDate |
| **Custom Records** | User-defined | Full Load | None |

---

## 2. Incremental Replication

### 2.1 How It Works

```
┌─────────────────────────────────────────────────────────┐
│                  Incremental Sync Flow                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Read last sync offset (lastModifiedDate)            │
│                     ↓                                    │
│  2. Build search filter:                                 │
│     lastModifiedDate >= offset                          │
│                     ↓                                    │
│  3. Execute search with pagination                       │
│                     ↓                                    │
│  4. Process records (extract, transform)                │
│                     ↓                                    │
│  5. Update offset to max(lastModifiedDate)              │
│                     ↓                                    │
│  6. Store offset for next run                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Supported Objects

| Category | Objects | Incremental Field |
|----------|---------|-------------------|
| Transaction | 37 types | lastModifiedDate |
| Item | 24 types | lastModifiedDate |
| Delete | All | deletedDate |

### 2.3 Search Filter Example

```java
// TransactionSearchBasic with lastModifiedDate filter
TransactionSearchBasic searchBasic = new TransactionSearchBasic();
SearchDateField lastModified = new SearchDateField();
lastModified.setOperator(SearchDateFieldOperator.ON_OR_AFTER);
lastModified.setSearchValue(offsetDate);
searchBasic.setLastModifiedDate(lastModified);
```

---

## 3. Full Load Replication

### 3.1 How It Works

```
┌─────────────────────────────────────────────────────────┐
│                   Full Load Sync Flow                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Execute search (no date filter)                     │
│                     ↓                                    │
│  2. Retrieve all records with pagination                │
│                     ↓                                    │
│  3. Replace destination table                           │
│     (or merge with deduplication)                       │
│                     ↓                                    │
│  4. Record sync timestamp                               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Current Full Load Objects (67)

These objects are currently synced as full load:

| Category | Count | Examples |
|----------|-------|----------|
| Setup/Reference | 50 | Account, Department, Location, Term |
| Entities (could be incremental) | 17 | Customer, Vendor, Employee, Contact |

### 3.3 Objects with Incremental Potential

These 17 objects have `lastModifiedDate` but are implemented as full load:

| Object | Impact | Priority |
|--------|--------|----------|
| Customer | High (large datasets) | P1 |
| Vendor | High (large datasets) | P1 |
| Contact | High (large datasets) | P1 |
| Employee | Medium | P2 |
| Partner | Medium | P2 |
| SupportCase | Medium | P2 |
| Issue | Medium | P2 |
| CalendarEvent | Low | P3 |
| PhoneCall | Low | P3 |
| Message | Low | P3 |
| Note | Low | P3 |
| File | Low | P3 |
| GiftCertificate | Low | P3 |
| Solution | Low | P3 |
| Paycheck | Low | P3 |
| TimeBill | Low | P3 |
| TimeEntry | Low | P3 |

---

## 4. Delete Tracking

### 4.1 GetDeleted Operation

```
┌─────────────────────────────────────────────────────────┐
│                  Delete Tracking Flow                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Call getDeleted with deletedDate filter             │
│                     ↓                                    │
│  2. Receive list of deleted record references           │
│     - internalId                                         │
│     - recordType                                         │
│     - deletedDate                                        │
│                     ↓                                    │
│  3. Propagate deletes to destination                    │
│                     ↓                                    │
│  4. Update deletedDate offset                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Supported Record Types for Delete Tracking

All standard record types that support deletion can be tracked.

---

## 5. Poll Modes

### 5.1 Basic Search

- Uses SearchBasic classes
- Simple field-based filtering
- Good for standard use cases

### 5.2 Saved Search

- Execute pre-configured NetSuite saved searches
- More complex filtering logic
- Includes joined data
- Requires Saved Search permission

### 5.3 Advanced Search

- Combines SearchBasic with SearchRow
- Return specific columns only
- Join multiple record types
- Most flexible but complex

---

## 6. Pagination Strategies

### 6.1 Search More with ID

```
1. Initial search returns searchId
2. Use searchMoreWithId(searchId, pageIndex)
3. Continue until all pages retrieved
```

### 6.2 Page Size Limits

| Operation | Default | Maximum |
|-----------|---------|---------|
| Search | 1000 | 1000 |
| Get | 10 | 1000 |
| GetList | 10 | 1000 |

---

## 7. Offset Management

### 7.1 Historical Offset Structure

```json
{
  "lastModifiedDate": "2026-01-15T10:30:00Z",
  "pageIndex": 0,
  "searchId": null
}
```

### 7.2 Offset Fields by Category

| Category | Offset Field | Type |
|----------|--------------|------|
| TRANSACTION | lastModifiedDate | DateTime |
| ITEM | lastModifiedDate | DateTime |
| DELETE | deletedDate | DateTime |
| STANDARD_FULL_LOAD | (none) | N/A |
| CUSTOM | (none) | N/A |

---

## 8. Improvement Opportunities

### 8.1 Enable Incremental for Standard Objects

**Impact**: Significant reduction in sync time and API usage

| Object | Current | Proposed |
|--------|---------|----------|
| Customer | Full | Incremental (lastModifiedDate) |
| Vendor | Full | Incremental (lastModifiedDate) |
| Contact | Full | Incremental (lastModifiedDate) |
| Employee | Full | Incremental (lastModifiedDate) |

### 8.2 SuiteQL Support

**Impact**: More efficient queries, better filtering

```sql
-- Example SuiteQL for incremental Customer sync
SELECT id, companyname, email, lastmodifieddate
FROM customer
WHERE lastmodifieddate >= TO_DATE('2026-01-01', 'YYYY-MM-DD')
ORDER BY lastmodifieddate
```

### 8.3 REST API for Additional Fields

**Impact**: Access to more incremental-capable objects

```
GET /services/rest/record/v1/customer
?q=lastModifiedDate AFTER 2026-01-01
```

---

## 9. Best Practices

### 9.1 Sync Frequency Recommendations

| Object Type | Recommended Frequency |
|-------------|----------------------|
| Transactions | Every 5-15 minutes |
| Items | Every 15-30 minutes |
| Entities (Full) | Every 1-6 hours |
| Setup Data | Daily |
| Delete Tracking | Every 15-30 minutes |

### 9.2 Error Handling

- Retry transient failures with exponential backoff
- Track failed records for manual review
- Maintain watermarks for resumable syncs

### 9.3 Performance Optimization

- Use Advanced Search to select only needed columns
- Batch API calls when possible
- Respect concurrency limits
