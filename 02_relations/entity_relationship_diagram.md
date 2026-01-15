# NetSuite Entity Relationship Diagrams

This document contains Mermaid diagrams showing the relationships between key NetSuite objects.

## 1. Core Entity Relationships

```mermaid
erDiagram
    Customer ||--o{ Contact : has
    Customer ||--o{ SalesOrder : places
    Customer ||--o{ Invoice : receives
    Customer }|--|| Subsidiary : belongs_to
    Customer }|--o| CustomerCategory : categorized_by
    Customer }|--o| CustomerStatus : has_status
    Customer }|--o| Term : payment_terms
    Customer }|--o| PriceLevel : pricing
    Customer }|--o| Employee : sales_rep

    Vendor ||--o{ Contact : has
    Vendor ||--o{ PurchaseOrder : receives
    Vendor ||--o{ VendorBill : sends
    Vendor }|--|| Subsidiary : belongs_to
    Vendor }|--o| VendorCategory : categorized_by
    Vendor }|--o| Term : payment_terms

    Employee }|--|| Subsidiary : belongs_to
    Employee }|--o| Department : works_in
    Employee }|--o| Location : located_at
    Employee }|--o| Employee : reports_to
```

## 2. Sales Order Flow

```mermaid
flowchart TD
    subgraph SalesProcess[Sales Process]
        OPP[Opportunity]
        EST[Estimate/Quote]
        SO[SalesOrder]
        IF[ItemFulfillment]
        INV[Invoice]
        CP[CustomerPayment]
    end

    OPP -->|transform| EST
    EST -->|transform| SO
    SO -->|transform| IF
    SO -->|transform| INV
    INV -->|apply| CP

    subgraph Entities[Entities]
        CUST[Customer]
        ITEM[Item]
        LOC[Location]
    end

    CUST --> SO
    ITEM --> SO
    LOC --> IF
```

## 3. Purchase Order Flow

```mermaid
flowchart TD
    subgraph PurchaseProcess[Purchase Process]
        PO[PurchaseOrder]
        IR[ItemReceipt]
        VB[VendorBill]
        VP[VendorPayment]
    end

    PO -->|transform| IR
    PO -->|transform| VB
    VB -->|apply| VP

    subgraph Entities[Entities]
        VEND[Vendor]
        ITEM[Item]
        LOC[Location]
        ACCT[Account]
    end

    VEND --> PO
    ITEM --> PO
    LOC --> IR
    ACCT --> VP
```

## 4. Item Hierarchy

```mermaid
erDiagram
    InventoryItem ||--o{ ItemVendor : supplied_by
    InventoryItem ||--o{ ItemLocation : stocked_at
    InventoryItem ||--o{ PricingMatrix : priced_at
    InventoryItem }|--|| Account : asset_account
    InventoryItem }|--|| Account : cogs_account
    InventoryItem }|--|| Account : income_account
    InventoryItem }|--o| UnitsType : measured_in
    InventoryItem }|--|| Subsidiary : belongs_to

    AssemblyItem ||--|{ BillOfMaterials : composed_of
    AssemblyItem }|--o| ManufacturingRouting : manufactured_via

    KitItem ||--|{ KitMember : contains
    
    ItemVendor }|--|| Vendor : vendor_ref
    ItemLocation }|--|| Location : location_ref
    PricingMatrix }|--|| PriceLevel : price_level
    BillOfMaterials }|--|| InventoryItem : component
```

## 5. Organizational Structure (OneWorld)

```mermaid
flowchart TD
    subgraph Organization[Organization Structure]
        ROOT[Root Subsidiary]
        SUB1[Subsidiary A]
        SUB2[Subsidiary B]
        SUB1A[Sub-Subsidiary A1]
    end

    ROOT --> SUB1
    ROOT --> SUB2
    SUB1 --> SUB1A

    subgraph Dimensions[Classification Dimensions]
        DEPT[Department]
        LOC[Location]
        CLASS[Classification]
    end

    SUB1 --> DEPT
    SUB1 --> LOC
    SUB1 --> CLASS

    subgraph Entities[Entities]
        CUST[Customer]
        VEND[Vendor]
        EMP[Employee]
        ACCT[Account]
    end

    SUB1 --> CUST
    SUB1 --> VEND
    SUB1 --> EMP
    SUB1 --> ACCT
```

## 6. Transaction Line Items

```mermaid
erDiagram
    Transaction ||--|{ TransactionLine : contains
    TransactionLine }|--|| Item : references
    TransactionLine }|--o| Location : at_location
    TransactionLine }|--o| Department : in_department
    TransactionLine }|--o| Class : classified_as
    TransactionLine }|--o| TaxCode : taxed_by

    Transaction }|--|| Subsidiary : belongs_to
    Transaction }|--o| Customer : for_customer
    Transaction }|--o| Vendor : from_vendor
    Transaction }|--|| Currency : in_currency
```

## 7. Accounting Relationships

```mermaid
erDiagram
    JournalEntry ||--|{ JournalEntryLine : contains
    JournalEntryLine }|--|| Account : debits_credits
    JournalEntryLine }|--o| Department : in_department
    JournalEntryLine }|--o| Location : at_location
    JournalEntryLine }|--o| Class : classified_as
    JournalEntryLine }|--o| Customer : for_customer
    JournalEntryLine }|--o| Vendor : from_vendor

    Account }|--o| Account : parent_account
    Account }|--|| Subsidiary : belongs_to
    Account }|--o| Currency : in_currency

    JournalEntry }|--|| Subsidiary : belongs_to
    JournalEntry }|--|| Currency : in_currency
```

## 8. Return and Credit Flow

```mermaid
flowchart TD
    subgraph Returns[Return Process]
        SO[SalesOrder]
        RA[ReturnAuthorization]
        CM[CreditMemo]
        CR[CashRefund]
    end

    SO -->|return| RA
    RA -->|transform| CM
    RA -->|transform| CR

    subgraph Application[Credit Application]
        INV[Invoice]
        CP[CustomerPayment]
    end

    CM -->|apply to| INV
    CM -->|apply to| CP
```

## 9. Custom Record Relationships

```mermaid
erDiagram
    CustomRecord ||--o{ CustomField : has
    CustomField }|--o| Customer : references
    CustomField }|--o| Transaction : references
    CustomField }|--o| Item : references
    CustomField }|--o| CustomRecord : references

    CustomRecord ||--o{ CustomSublist : contains
    CustomSublist }|--|| CustomRecord : child_record
```

## 10. Complete Transaction Entity Map

```mermaid
flowchart LR
    subgraph Entities[Entities]
        C[Customer]
        V[Vendor]
        E[Employee]
    end

    subgraph SalesTransactions[Sales]
        EST[Estimate]
        SO[SalesOrder]
        INV[Invoice]
        CS[CashSale]
        CM[CreditMemo]
    end

    subgraph PurchaseTransactions[Purchase]
        PO[PurchaseOrder]
        VB[VendorBill]
        VC[VendorCredit]
    end

    subgraph InventoryTransactions[Inventory]
        IF[ItemFulfillment]
        IR[ItemReceipt]
        IA[InventoryAdjustment]
        IT[InventoryTransfer]
    end

    subgraph FinancialTransactions[Financial]
        JE[JournalEntry]
        DEP[Deposit]
        CHK[Check]
    end

    C --> EST
    C --> SO
    C --> INV
    C --> CS
    C --> CM

    V --> PO
    V --> VB
    V --> VC

    E --> JE
```
