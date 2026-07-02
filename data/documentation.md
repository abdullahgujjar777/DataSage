# DataSage — Auto-Generated Documentation

_Generated: 2026-07-02T08:49:57.931639+00:00_

## returns

**Purpose:** This table records product return transactions made by customers. It captures which order and order line were returned, the return date, reason, current status, and the refund amount.

**Columns:**
- `return_id`: Unique identifier for each return record
- `order_id`: Identifier of the original order that the return belongs to
- `order_item_id`: Identifier of the specific line item in the order that is being returned
- `return_date`: Date and time when the return was processed
- `reason`: Reason code supplied by the customer for the return (e.g., changed_mind, wrong_item)
- `status`: Current processing state of the return (e.g., approved, refunded)
- `refund_amount`: Monetary amount refunded to the customer

**Relationships:** order_id links to orders.order_id; order_item_id links to order_items.order_item_id.

**Business Value:** Enables analysis of why products are returned, how much money is refunded, and which orders or items generate the most returns.

**⚠️ Ambiguity Flags:**
- `status`: status here records the return's processing stage (approved, refunded, etc.). Other tables also have a status column (suppliers, marketing_campaigns, customers, orders, products) with different value sets such as active, completed, cancelled; there is no declared relationship, so the shared name likely refers to unrelated concepts.
- `refund_amount`: refund_amount is a monetary value, but the currency (e.g., USD, EUR) is not indicated in the sample data.

## suppliers

**Purpose:** This table lists the companies that provide products to the business. It stores each supplier’s name, country, contact email, and current operational status.

**Columns:**
- `supplier_id`: Unique identifier for each supplier
- `supplier_name`: Legal name of the supplier
- `country`: Country where the supplier is located
- `contact_email`: Email address for contacting the supplier
- `status`: Current relationship status of the supplier (e.g., active)

**Relationships:** 

**Business Value:** Supports sourcing analysis, such as identifying active suppliers by country and monitoring supplier availability.

**⚠️ Ambiguity Flags:**
- `status`: status here indicates whether the supplier relationship is active. Other tables also have a status column (returns, marketing_campaigns, customers, orders, products) with different meanings like approved, completed, cancelled; no declared link suggests the same name is used generically.
- `country`: country records the supplier’s location. Customers also have a country column, but the sampled values do not overlap, indicating the two columns refer to different entities (supplier location vs. customer residence) without a declared relationship.

## inventory

**Purpose:** This table tracks the stock levels for each product. It records the quantity on hand, the reorder threshold, and the last time the record was updated.

**Columns:**
- `inventory_id`: Unique identifier for each inventory record
- `product_id`: Identifier of the product whose stock is being tracked
- `quantity_on_hand`: Number of units of the product currently in stock
- `reorder_threshold`: Stock level at which a new order should be placed
- `last_updated`: Timestamp of the most recent inventory count update

**Relationships:** product_id links to products.product_id.

**Business Value:** Enables monitoring of product availability and triggers for replenishment based on stock thresholds.

## marketing_campaigns

**Purpose:** This table logs marketing campaigns run by the company. It tracks each campaign’s name, channel, start and end dates, budget, and current status.

**Columns:**
- `campaign_id`: Unique identifier for each campaign
- `campaign_name`: Descriptive name of the campaign
- `channel`: Marketing channel used for the campaign (e.g., affiliate, social_media)
- `start_date`: Date when the campaign began
- `end_date`: Date when the campaign ended or null if ongoing
- `budget`: Planned spend for the campaign
- `status`: Current state of the campaign (e.g., active, completed, paused)

**Relationships:** 

**Business Value:** Allows assessment of spend effectiveness by channel and time period, and tracking of campaign lifecycles.

**⚠️ Ambiguity Flags:**
- `channel`: channel here refers to marketing medium such as affiliate or social_media. Orders also have a channel column (in_store, marketplace, mobile_app, web) with no overlapping values, indicating the same name describes different concepts without a declared link.
- `status`: status here indicates the campaign's lifecycle stage. Other tables (returns, suppliers, customers, orders, products) also have a status column with unrelated value sets; no declared relationship suggests a generic use of the term.
- `budget`: budget is a monetary amount, but the currency is not specified in the sample data.

## customers

**Purpose:** This table contains information about individual customers. It records their contact details, signup date, country, segmentation label, and account status.

**Columns:**
- `customer_id`: Unique identifier for each customer
- `email`: Customer's email address
- `first_name`: Customer's given name
- `last_name`: Customer's family name
- `signup_date`: Date when the customer created an account
- `country`: Country of residence of the customer
- `segment`: Business-assigned customer segment (e.g., at_risk, new, regular, high_value)
- `status`: Current account status (e.g., active, inactive, churned)

**Relationships:** 

**Business Value:** Supports segmentation analysis to understand customer value, churn risk, and geographic distribution.

**⚠️ Ambiguity Flags:**
- `status`: status here reflects the account's condition. Other tables (returns, suppliers, marketing_campaigns, orders, products) also have a status column with different meanings; no declared link indicates the term is used generically across tables.
- `country`: country records the customer's residence. Suppliers also have a country column for supplier location, but the sampled values do not overlap, suggesting the columns refer to different entities without a declared relationship.
- `segment`: segment categories are business-defined labels; the exact criteria for each label are not provided in the sample, making the meaning of each segment ambiguous.

## orders

**Purpose:** This table records each purchase order placed by a customer. It tracks the order’s date, sales channel, status, and total monetary amount.

**Columns:**
- `order_id`: Unique identifier for each order
- `customer_id`: Identifier of the customer who placed the order
- `order_date`: Timestamp when the order was created
- `status`: Current fulfillment state of the order (e.g., cancelled, refunded)
- `channel`: Sales channel through which the order was placed (e.g., in_store, marketplace, mobile_app, web)
- `total_amount`: Total monetary value of the order

**Relationships:** customer_id links to customers.customer_id.

**Business Value:** Enables analysis of sales volume, revenue by channel, and order fulfilment performance.

**⚠️ Ambiguity Flags:**
- `status`: status here describes the order's fulfillment stage. Other tables (returns, suppliers, marketing_campaigns, customers, products) also have a status column with unrelated value sets; no declared link suggests a generic usage.
- `channel`: channel here indicates where the purchase was made (in_store, marketplace, mobile_app, web). Marketing_campaigns also has a channel column (affiliate, email, paid_search, social_media) with no overlapping values, so the shared name likely refers to different concepts.
- `total_amount`: total_amount is a monetary figure, but the currency is not indicated in the sample.

## order_items

**Purpose:** This table breaks down each order into its constituent line items. It records which product was ordered, the quantity, and the unit price.

**Columns:**
- `order_item_id`: Unique identifier for each line item
- `order_id`: Identifier of the order to which this line item belongs
- `product_id`: Identifier of the product being purchased
- `quantity`: Number of units of the product in this line item
- `unit_price`: Price per unit of the product for this line item

**Relationships:** order_id links to orders.order_id; product_id links to products.product_id.

**Business Value:** Supports detailed revenue analysis per product and quantity sold per order.

**⚠️ Ambiguity Flags:**
- `unit_price`: unit_price is a monetary amount, but the currency is not specified in the sample data.

## products

**Purpose:** This table catalogs the products the company sells. It stores each product’s name, category, price, status, and the supplier that provides it.

**Columns:**
- `product_id`: Unique identifier for each product
- `product_name`: Descriptive name of the product
- `category`: Broad grouping of the product (e.g., beauty, toys, home_goods, sports)
- `price`: Standard selling price of the product
- `status`: Current availability status of the product (e.g., active, discontinued, out_of_stock)
- `supplier_id`: Identifier of the supplier that provides this product

**Relationships:** supplier_id links to suppliers.supplier_id.

**Business Value:** Enables product portfolio analysis, pricing strategy, and supplier performance tracking.

**⚠️ Ambiguity Flags:**
- `status`: status here reflects product availability. Other tables (returns, suppliers, marketing_campaigns, customers, orders) also have a status column with unrelated meanings; no declared link indicates a generic use of the term.
- `price`: price is a monetary figure, but the currency is not indicated in the sample.
