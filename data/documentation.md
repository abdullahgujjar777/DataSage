# DataSage — Auto-Generated Documentation

_Generated: 2026-06-29T17:35:21.174824+00:00_

## marketing_campaigns

**Purpose:** Tracks each marketing campaign with its details and outcomes.

**Columns:**
- `campaign_id`: Unique identifier for a marketing campaign.
- `campaign_name`: Descriptive name given to the campaign.
- `channel`: Marketing channel used for the campaign (e.g., social_media, affiliate, paid_search).
- `start_date`: Date the campaign began or is scheduled to begin.
- `end_date`: Date the campaign ended or is scheduled to end; may be null for ongoing campaigns.
- `budget`: Monetary budget allocated to the campaign.
- `status`: Current lifecycle status of the campaign (e.g., active, completed, paused).

**Relationships:** None

**Business Value:** Enables analysis of campaign performance, budgeting, and channel effectiveness across time.

**⚠️ Ambiguity Flags:**
- `channel`: The column name 'channel' also appears in the orders table with different observed values (in_store, marketplace, mobile_app). No foreign key links; meaning is ambiguous across tables.
- `status`: The column name 'status' appears in customers, orders, and products tables with differing value sets and no foreign key relationship, so its specific meaning is ambiguous.

## customers

**Purpose:** Stores basic profile information for each customer.

**Columns:**
- `customer_id`: Unique identifier for a customer.
- `email`: Customer's email address, used as a contact identifier.
- `first_name`: Customer's given name.
- `last_name`: Customer's family name.
- `signup_date`: Date the customer account was created.
- `country`: Country associated with the customer.
- `segment`: Marketing segment classification (e.g., new, at_risk, regular, high_value).
- `status`: Current account status (e.g., active, inactive, churned).

**Relationships:** None

**Business Value:** Provides a basis for segmentation, targeting, and lifecycle management of the customer base.

**⚠️ Ambiguity Flags:**
- `status`: The column name 'status' also appears in marketing_campaigns, orders, and products tables with different value sets and no foreign key relationship, making its precise meaning ambiguous across tables.

## orders

**Purpose:** Records each purchase transaction made by customers.

**Columns:**
- `order_id`: Unique identifier for an order.
- `customer_id`: Reference to the customer who placed the order.
- `order_date`: Timestamp when the order was created.
- `status`: Current state of the order (e.g., cancelled, refunded).
- `channel`: Sales channel through which the order was placed (e.g., in_store, marketplace, mobile_app).
- `total_amount`: Total monetary value of the order.

**Relationships:** customer_id references customers.customer_id

**Business Value:** Allows tracking of sales volume, channel performance, and order fulfillment outcomes.

**⚠️ Ambiguity Flags:**
- `status`: The column name 'status' also exists in marketing_campaigns, customers, and products tables with differing values and no foreign key relationship; its meaning is ambiguous across tables.
- `channel`: The column name 'channel' also appears in marketing_campaigns with different observed values (social_media, affiliate, paid_search). No foreign key links; meaning is ambiguous across tables.

## order_items

**Purpose:** Details the individual products included in each order.

**Columns:**
- `order_item_id`: Unique identifier for an order line item.
- `order_id`: Reference to the order that contains this item.
- `product_id`: Reference to the product being purchased.
- `quantity`: Number of units of the product in this line item.
- `unit_price`: Price per unit of the product at the time of the order.

**Relationships:** order_id references orders.order_id; product_id references products.product_id

**Business Value:** Enables analysis of product-level sales, average order value, and inventory demand.

## products

**Purpose:** Catalogues items that can be sold.

**Columns:**
- `product_id`: Unique identifier for a product.
- `product_name`: Descriptive name of the product.
- `category`: Category or group the product belongs to.
- `price`: Standard selling price of the product.
- `status`: Current availability status (e.g., active, discontinued, out_of_stock).

**Relationships:** product_id referenced by order_items.product_id

**Business Value:** Supports product inventory management, pricing strategy, and category performance reporting.

**⚠️ Ambiguity Flags:**
- `status`: The column name 'status' also appears in marketing_campaigns, customers, and orders tables with different value sets and no foreign key relationship, so its precise meaning is ambiguous across tables.
