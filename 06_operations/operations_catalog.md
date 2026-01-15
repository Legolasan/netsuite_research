# NetSuite API Operations Catalog

This document catalogs all available API operations and their current implementation status.

## 1. Overview

### SOAP Web Services Operations

| Category | Current | Available | Gap |
|----------|---------|-----------|-----|
| Read Operations | 4 | 4 | None |
| Write Operations | 0 | 5 | 5 |
| Transform Operations | 0 | 1 | 1 |
| Relationship Operations | 0 | 2 | 2 |
| Async Operations | 0 | 5 | 5 |

---

## 2. Currently Implemented Operations

### 2.1 Search Operations

| Operation | Description | Usage | Status |
|-----------|-------------|-------|--------|
| `search` | Execute a search query | Primary data extraction | ✅ Implemented |
| `searchMore` | Get next page of results | Pagination | ✅ Implemented |
| `searchMoreWithId` | Get specific page by search ID | Efficient pagination | ✅ Implemented |

### 2.2 Delete Tracking

| Operation | Description | Usage | Status |
|-----------|-------------|-------|--------|
| `getDeleted` | Get deleted records | Delete tracking | ✅ Implemented |

---

## 3. Available but Not Implemented

### 3.1 Single Record Operations

| Operation | Description | Governance Cost | Priority |
|-----------|-------------|-----------------|----------|
| `get` | Get single record by ID | 5 units | Medium |
| `getList` | Get multiple records by IDs | 5 units/record | Medium |

### 3.2 Write Operations

| Operation | Description | Governance Cost | Priority |
|-----------|-------------|-----------------|----------|
| `add` | Create new record | 10 units | High |
| `addList` | Create multiple records | 10 units/record | High |
| `update` | Update existing record | 10 units | High |
| `updateList` | Update multiple records | 10 units/record | High |
| `upsert` | Create or update record | 10 units | Medium |
| `upsertList` | Create or update multiple | 10 units/record | Medium |
| `delete` | Delete record | 10 units | Low |
| `deleteList` | Delete multiple records | 10 units/record | Low |

### 3.3 Transform Operations

| Operation | Description | Use Cases | Priority |
|-----------|-------------|-----------|----------|
| `transform` | Convert record type | Quote→Order, Order→Invoice | Medium |

### 3.4 Relationship Operations

| Operation | Description | Use Cases | Priority |
|-----------|-------------|-----------|----------|
| `attach` | Link records | Files to records | Low |
| `detach` | Unlink records | Remove attachments | Low |

### 3.5 Async Operations

| Operation | Description | Use Cases | Priority |
|-----------|-------------|-----------|----------|
| `asyncAddList` | Async bulk create | Large imports | High |
| `asyncUpdateList` | Async bulk update | Bulk modifications | High |
| `asyncUpsertList` | Async bulk upsert | Large syncs | High |
| `asyncDeleteList` | Async bulk delete | Bulk cleanup | Low |
| `getAsyncResult` | Get async result | Check async status | High |

---

## 4. REST API Operations

### 4.1 Current REST Support

**Status**: Not Implemented

### 4.2 Available REST Operations

| Method | Endpoint Pattern | Description |
|--------|-----------------|-------------|
| GET | `/record/v1/{type}` | List records |
| GET | `/record/v1/{type}/{id}` | Get single record |
| POST | `/record/v1/{type}` | Create record |
| PATCH | `/record/v1/{type}/{id}` | Update record |
| DELETE | `/record/v1/{type}/{id}` | Delete record |
| POST | `/query/v1/suiteql` | Execute SuiteQL |

### 4.3 REST Advantages

| Feature | SOAP | REST |
|---------|------|------|
| Async Operations | Limited | Full support |
| SuiteQL | No | Yes |
| Newer Records | No | Yes |
| Subresources | Complex | Simple paths |
| Payload Size | Larger | Smaller (JSON) |

---

## 5. Operation Details

### 5.1 Search Operation

```xml
<!-- Request -->
<search>
  <searchRecord xsi:type="TransactionSearchBasic">
    <lastModifiedDate operator="onOrAfter">
      <searchValue>2026-01-01T00:00:00Z</searchValue>
    </lastModifiedDate>
  </searchRecord>
</search>

<!-- Response -->
<searchResponse>
  <searchResult>
    <status isSuccess="true"/>
    <totalRecords>1500</totalRecords>
    <pageSize>1000</pageSize>
    <totalPages>2</totalPages>
    <pageIndex>1</pageIndex>
    <searchId>WEBSERVICES_1234567890</searchId>
    <recordList>
      <!-- records -->
    </recordList>
  </searchResult>
</searchResponse>
```

### 5.2 GetDeleted Operation

```xml
<!-- Request -->
<getDeleted>
  <getDeletedFilter>
    <deletedDate operator="onOrAfter">
      <searchValue>2026-01-01T00:00:00Z</searchValue>
    </deletedDate>
    <type>
      <searchValue>invoice</searchValue>
    </type>
  </getDeletedFilter>
</getDeleted>

<!-- Response -->
<getDeletedResponse>
  <getDeletedResult>
    <status isSuccess="true"/>
    <deletedRecordList>
      <deletedRecord>
        <deletedDate>2026-01-15T10:30:00Z</deletedDate>
        <record internalId="12345" type="invoice"/>
      </deletedRecord>
    </deletedRecordList>
  </getDeletedResult>
</getDeletedResponse>
```

### 5.3 Add Operation (Not Implemented)

```xml
<!-- Request -->
<add>
  <record xsi:type="Customer">
    <companyName>Acme Corp</companyName>
    <email>contact@acme.com</email>
    <subsidiary internalId="1"/>
  </record>
</add>

<!-- Response -->
<addResponse>
  <writeResponse>
    <status isSuccess="true"/>
    <baseRef internalId="12345" type="customer"/>
  </writeResponse>
</addResponse>
```

### 5.4 Update Operation (Not Implemented)

```xml
<!-- Request -->
<update>
  <record xsi:type="Customer" internalId="12345">
    <email>newemail@acme.com</email>
  </record>
</update>

<!-- Response -->
<updateResponse>
  <writeResponse>
    <status isSuccess="true"/>
    <baseRef internalId="12345" type="customer"/>
  </writeResponse>
</updateResponse>
```

### 5.5 Transform Operation (Not Implemented)

```xml
<!-- Request: Convert SalesOrder to Invoice -->
<transform>
  <sourceRecord type="salesOrder" internalId="12345"/>
  <targetRecord type="invoice"/>
</transform>

<!-- Response -->
<transformResponse>
  <writeResponse>
    <status isSuccess="true"/>
    <baseRef internalId="67890" type="invoice"/>
  </writeResponse>
</transformResponse>
```

---

## 6. SuiteQL Operations (Not Implemented)

### 6.1 Query Syntax

```sql
-- Simple query
SELECT id, companyname, email
FROM customer
WHERE lastmodifieddate >= '2026-01-01'
ORDER BY lastmodifieddate

-- Join query
SELECT t.id, t.tranid, c.companyname
FROM transaction t
JOIN customer c ON t.entity = c.id
WHERE t.type = 'Invoice'
```

### 6.2 REST Endpoint

```
POST /services/rest/query/v1/suiteql

{
  "q": "SELECT id, companyname FROM customer WHERE lastmodifieddate >= '2026-01-01'"
}
```

---

## 7. Saved Search Execution

### 7.1 Current Support

**Status**: Partially implemented (via search parameters)

### 7.2 Saved Search Benefits

- Pre-defined complex queries
- Include formula fields
- Join multiple records
- Built-in business logic

---

## 8. Implementation Roadmap

### Phase 1: Enhance Read Operations (Quick Wins)

| Operation | Effort | Impact |
|-----------|--------|--------|
| `get` | Low | Enable single record fetch |
| `getList` | Low | Enable batch record fetch |
| Saved Search | Medium | Complex query support |

### Phase 2: Write Operations (High Value)

| Operation | Effort | Impact |
|-----------|--------|--------|
| `add` | Medium | Enable record creation |
| `update` | Medium | Enable record updates |
| `upsert` | Medium | Enable sync both ways |

### Phase 3: Advanced Operations

| Operation | Effort | Impact |
|-----------|--------|--------|
| `transform` | High | Enable workflow automation |
| Async operations | High | Enable bulk processing |
| REST API | High | Modern API access |

### Phase 4: Query Enhancements

| Operation | Effort | Impact |
|-----------|--------|--------|
| SuiteQL | Medium | Flexible queries |
| Analytics | High | Reporting data access |
