# NetSuite Object Relations

This document describes the relationships between NetSuite objects, including parent-child relationships, foreign key references, and sublist associations.

## 1. Core Entity Relationships

### 1.1 Customer Hierarchy

```
Customer
├── Contact (many)
├── CustomerAddress (sublist)
├── CustomerCurrency (sublist)
├── CustomerPartner (sublist)
├── CustomerSalesTeam (sublist)
├── CustomerSubsidiary (reference)
├── CustomerCategory (reference)
├── CustomerStatus (reference)
├── Term (reference)
├── PriceLevel (reference)
└── SalesRep (Employee reference)
```

### 1.2 Vendor Hierarchy

```
Vendor
├── Contact (many)
├── VendorAddress (sublist)
├── VendorCurrency (sublist)
├── VendorSubsidiary (reference)
├── VendorCategory (reference)
├── Term (reference)
├── Account (reference: expense, payables)
└── Currency (reference)
```

### 1.3 Employee Hierarchy

```
Employee
├── EmployeeAddress (sublist)
├── EmployeeRoles (sublist)
├── Department (reference)
├── Location (reference)
├── Subsidiary (reference)
├── Supervisor (Employee reference)
├── PayrollItem (many)
└── HcmJob (reference)
```

---

## 2. Transaction Relationships

### 2.1 Sales Order Flow

```
Estimate (Quote)
    ↓ transform
SalesOrder
├── Customer (reference)
├── Item (line items)
├── SalesOrderItem (sublist)
│   ├── Item (reference)
│   ├── Location (reference)
│   └── TaxCode (reference)
├── ShipAddress (sublist)
├── BillAddress (sublist)
├── Partner (sublist)
├── SalesTeam (sublist)
└── Subsidiary (reference)
    ↓ transform
ItemFulfillment
├── SalesOrder (reference: createdFrom)
├── Customer (reference)
├── ItemFulfillmentItem (sublist)
└── Package (sublist)
    ↓ transform
Invoice
├── SalesOrder (reference: createdFrom)
├── Customer (reference)
├── InvoiceItem (sublist)
├── GiftCertRedemption (sublist)
└── Installment (sublist)
    ↓ transform
CustomerPayment
├── Invoice (apply list)
├── Customer (reference)
└── PaymentMethod (reference)
```

### 2.2 Purchase Order Flow

```
PurchaseOrder
├── Vendor (reference)
├── Item (line items)
├── PurchaseOrderItem (sublist)
│   ├── Item (reference)
│   ├── Location (reference)
│   └── Customer (reference: dropship)
├── Expense (sublist)
└── Subsidiary (reference)
    ↓ transform
ItemReceipt
├── PurchaseOrder (reference: createdFrom)
├── Vendor (reference)
├── ItemReceiptItem (sublist)
└── LandedCost (sublist)
    ↓ transform
VendorBill
├── PurchaseOrder (reference: createdFrom)
├── Vendor (reference)
├── VendorBillItem (sublist)
├── VendorBillExpense (sublist)
└── Account (reference: payable)
    ↓ transform
VendorPayment
├── VendorBill (apply list)
├── Vendor (reference)
├── Account (reference)
└── VendorCredit (credit list)
```

### 2.3 Return Flow

```
ReturnAuthorization
├── Customer (reference)
├── SalesOrder (reference: createdFrom)
├── ReturnAuthorizationItem (sublist)
└── Location (reference)
    ↓ transform
CreditMemo
├── Customer (reference)
├── ReturnAuthorization (reference: createdFrom)
├── CreditMemoItem (sublist)
└── CreditMemoApply (sublist)
    OR
CashRefund
├── Customer (reference)
├── CashRefundItem (sublist)
└── PaymentMethod (reference)
```

---

## 3. Item Relationships

### 3.1 Inventory Item

```
InventoryItem
├── ItemVendor (sublist)
│   └── Vendor (reference)
├── ItemLocation (sublist)
│   └── Location (reference)
├── Pricing (matrix)
│   └── PriceLevel (reference)
├── Account (references)
│   ├── assetAccount
│   ├── cogsAccount
│   ├── incomeAccount
│   └── expenseAccount
├── TaxSchedule (reference)
├── UnitsType (reference)
├── Subsidiary (reference)
├── CustomForm (reference)
└── InventoryNumber (many - for serialized/lot)
```

### 3.2 Assembly Item

```
AssemblyItem
├── (all InventoryItem relationships)
├── BillOfMaterials (sublist)
│   ├── Component Item (reference)
│   ├── Quantity
│   └── Units
├── ManufacturingRouting (reference)
└── ManufacturingCostTemplate (reference)
```

### 3.3 Kit Item

```
KitItem
├── Member (sublist)
│   ├── Item (reference)
│   └── Quantity
├── Component (optional sublist)
└── Pricing (matrix)
```

---

## 4. Accounting Relationships

### 4.1 Account Hierarchy

```
Account
├── Parent (self-reference)
├── Subsidiary (reference)
├── Currency (reference)
├── Classification (reference)
├── Department (reference)
├── Location (reference)
└── Type (enum)
    ├── Bank
    ├── AccountsReceivable
    ├── AccountsPayable
    ├── Income
    ├── Expense
    ├── Equity
    └── ...
```

### 4.2 Journal Entry

```
JournalEntry
├── Subsidiary (reference)
├── Currency (reference)
├── JournalEntryLine (sublist)
│   ├── Account (reference)
│   ├── Debit/Credit
│   ├── Department (reference)
│   ├── Location (reference)
│   ├── Class (reference)
│   ├── Customer (reference)
│   └── Vendor (reference)
└── AccountingBook (reference)
```

---

## 5. Organizational Hierarchy

### 5.1 Subsidiary Structure

```
Subsidiary (OneWorld)
├── Parent (self-reference)
├── Currency (reference)
├── Address (sublist)
├── Account (many)
├── Department (many)
├── Location (many)
├── Employee (many)
├── Customer (many - via CustomerSubsidiary)
└── Vendor (many - via VendorSubsidiary)
```

### 5.2 Classification Dimensions

```
Transaction/Record
├── Subsidiary (reference)
├── Department (reference)
├── Class/Classification (reference)
└── Location (reference)
```

---

## 6. Foreign Key Reference Summary

| Object | Common Foreign Keys |
|--------|---------------------|
| **Transaction** | subsidiary, currency, customer/vendor, location, department, class |
| **Customer** | subsidiary, salesRep, category, status, terms, priceLevel |
| **Vendor** | subsidiary, category, terms, expenseAccount |
| **Item** | subsidiary, unitsType, assetAccount, cogsAccount, incomeAccount |
| **Employee** | subsidiary, department, location, supervisor, payrollItem |
| **Contact** | company (customer/vendor), subsidiary |
| **Account** | parent, subsidiary, currency |

---

## 7. Sublist Types

### 7.1 Line Item Sublists
- TransactionItem (items on transactions)
- TransactionExpense (expenses on transactions)
- Address (shipping/billing addresses)

### 7.2 Association Sublists
- CustomerContact (contacts on customer)
- VendorAddress (addresses on vendor)
- ItemVendor (vendors for item)
- ItemLocation (locations for item)

### 7.3 Application Sublists
- CustomerPaymentApply (invoices paid)
- VendorPaymentApply (bills paid)
- CreditMemoApply (credits applied)
- DepositApplication (deposits applied)

---

## 8. Transform Relationships

| Source | Target | Operation |
|--------|--------|-----------|
| Estimate | SalesOrder | Transform |
| SalesOrder | Invoice | Transform |
| SalesOrder | ItemFulfillment | Transform |
| SalesOrder | CashSale | Transform |
| PurchaseOrder | ItemReceipt | Transform |
| PurchaseOrder | VendorBill | Transform |
| ReturnAuthorization | CreditMemo | Transform |
| ReturnAuthorization | CashRefund | Transform |
| Quote | SalesOrder | Transform |
| Opportunity | Estimate | Transform |
| VendorReturnAuth | VendorCredit | Transform |

---

## 9. Custom Record Relationships

Custom records can have relationships defined via:

1. **Custom Fields** - List/Record type fields referencing standard or custom records
2. **Custom Sublists** - Child records with parent reference
3. **Record References** - Links to standard records

```
CustomRecord
├── CustomField (List/Record type)
│   └── Target Record (Customer, Transaction, Item, etc.)
├── CustomSublist
│   └── Child CustomRecord
└── Parent (reference to parent custom record)
```
