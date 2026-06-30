# DataSage — Auto-Generated Documentation

_Generated: 2026-06-30T16:21:38.044946+00:00_

## marketing_campaigns

**Purpose:** This table records marketing campaigns that the company runs. It tracks each campaign's name, channel, start and end dates, budget, and current status such as active, paused, or completed.

**Columns:**
- `campaign_id`: Unique identifier for each campaign.
- `campaign_name`: Descriptive name of the campaign.
- `channel`: The marketing channel used for the campaign (e.g., affiliate, email, paid search, social media).
- `start_date`: Date the campaign began.
- `end_date`: Date the campaign ended or is planned to end.
- `budget`: Planned spending amount for the campaign (currency not specified).
- `status`: Current lifecycle state of the campaign (e.g., active, paused, completed).

**Relationships:** None.

**Business Value:** Answers which marketing channels are being used, how much is allocated to each campaign, and which campaigns are currently active, paused, or completed.

**⚠️ Ambiguity Flags:**
- `channel`: The channel column lists marketing distribution methods (affiliate, email, paid_search, social_media); the same‑named column in orders lists purchase locations (in_store, marketplace, mobile_app, web) and there is no declared link, so they describe different things.
- `status`: The status column appears in several tables with different value sets; only the word “active” overlaps, which is a generic term, so the column likely has unrelated meanings across tables.
- `budget`: The budget amount is given without any currency unit, so the monetary unit is unclear.

## customers

**Purpose:** This table stores information about individual customers. It tracks each customer's contact details, signup date, country, segmentation label, and current account status.

**Columns:**
- `customer_id`: Unique identifier for each customer.
- `email`: Customer's email address.
- `first_name`: Given name of the customer.
- `last_name`: Family name of the customer.
- `signup_date`: Date the customer created their account.
- `country`: Country or territory associated with the customer.
- `segment`: Label indicating the customer's marketing segment (e.g., new, regular, high_value, at_risk).
- `status`: Current account state such as active, inactive, or churned.

**Relationships:** None.

**Business Value:** Enables queries about how many customers are in each segment, which countries they belong to, and how many are active versus churned, supporting retention and targeting analysis.

**⚠️ Ambiguity Flags:**
- `status`: The status column appears in several tables with different value sets; only the word “active” overlaps, which is a generic term, so the column likely has unrelated meanings across tables.
- `segment`: The segment values (new, regular, high_value, at_risk) are not defined in the data, so the criteria for each label are unclear.

## orders

**Purpose:** This table records each purchase order placed by customers. It tracks the order’s customer, date and time, sales channel, current fulfillment status, and total monetary amount.

**Columns:**
- `order_id`: Unique identifier for each order.
- `customer_id`: Reference to the customer who placed the order.
- `order_date`: Date and time when the order was created.
- `status`: Current fulfillment state of the order (e.g., cancelled, refunded, delivered).
- `channel`: Sales channel where the order was made (e.g., in_store, marketplace, mobile_app, web).
- `total_amount`: Total monetary value of the order (currency not specified).

**Relationships:** customer_id links to customers.customer_id.

**Business Value:** Shows which sales channels generate revenue, how many orders are cancelled or refunded, and total sales amount over time.

**⚠️ Ambiguity Flags:**
- `channel`: The channel column lists purchase locations (in_store, marketplace, mobile_app, web); the same‑named column in marketing_campaigns lists marketing distribution methods (affiliate, email, paid_search, social_media) and there is no declared link, so they describe different things.
- `status`: The status column appears in several tables with different value sets; only the word “active” overlaps, which is a generic term, so the column likely has unrelated meanings across tables.
- `total_amount`: The total amount is provided without a currency unit, making the monetary unit unclear.

## order_items

**Purpose:** This table lists the individual line items that belong to each order. It records which product was sold, how many units, and the price per unit at the time of the order.

**Columns:**
- `order_item_id`: Unique identifier for each line item.
- `order_id`: Reference to the order this line belongs to.
- `product_id`: Reference to the product that was purchased.
- `quantity`: Number of units of the product in this line item.
- `unit_price`: Price per single unit (currency not specified).

**Relationships:** order_id links to orders.order_id. product_id links to products.product_id.

**Business Value:** Allows calculation of revenue per product, average unit price, and quantity sold per order.

**⚠️ Ambiguity Flags:**
- `unit_price`: The unit price is given without a currency unit, so the monetary unit is unclear.

## products

**Purpose:** This table catalogs the products that can be sold. It records each product’s name, category, price, and availability status.

**Columns:**
- `product_id`: Unique identifier for each product.
- `product_name`: Descriptive name of the product.
- `category`: Broad classification such as beauty, toys, home_goods, sports.
- `price`: Standard price of the product (currency not specified).
- `status`: Current availability state (e.g., active, discontinued, out_of_stock).

**Relationships:** None.

**Business Value:** Supports analysis of product pricing across categories and which products are currently sellable versus discontinued or out of stock.

**⚠️ Ambiguity Flags:**
- `status`: The status column appears in several tables with different value sets; only the word “active” overlaps, which is a generic term, so the column likely has unrelated meanings across tables.
- `price`: The price is listed without a currency unit, making the monetary unit unclear.
