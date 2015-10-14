# Encompass Theme System

Encompass uses a theming system for customization. This document details
some specifics about it.

## Brush Color Workaround

Becuse there is no easy way to set the color of text in columns of a
table widget, we use a workaround. Rules for text in tables are set
using the CSS rule for properties of the class `Item`.

## Customizable Objects

These are the names that one might define a color for in a stylesheet.

### Text in Trees and Tables

The following table lists properties of the `Item` class and describes where their
rules apply. An example of what data may be in the cell is provided.

|Name                        |Description       |Example|
|----------------------------|------------------|-------|
|`Item[role="text_item"]`    |Generic color for text in a column. Used as a fallback if a more specific color is not defined.|(Something)|
|`Item[role="date"]`           |Date that a transaction happened.|2015-07-02 14:55|
|`Item[role="amount"]`         |Amount of a credited transaction.|+0.01|
|`Item[role="amount_negative"]`|Amount of a debited transaction.|-0.01|
|`Item[role="label_default"]`  |Default label for a transaction.|<MVqWPDwuLMC6qJnotrVTh5JP3etCCxuSpP|
|`Item[role="label"]`          |Set label for a transaction.   |Birthday present for Joe|
|`Item[role="balance"]`        |Wallet balance.                |2.981|
|`Item[role="address"]`        |Address involved in a transaction.|MVqWPDwuLMC6qJnotrVTh5JP3etCCxuSpP|
|`Item[role="tx_count"]`       |Number of transactions involving an address.|4|
|`Item[role="yes"]`            |Boolean value; True|Yes|
|`Item[role="no"]`             |Boolean value; False|No|


### Display Areas

These are areas that are displayed. For example, a theme is likely to change 
the `background-color` rule for these.

|Name           |Description|
|---------------|-----------|
|`#main_window`  |Main window of the wallet.|
|`#history_tab`  |Tab showing the wallet history.|
|`#send_tab`     |Tab for sending coins.|
|`#receive_tab`  |Tab for getting an address or creating a payment request.|
|`#addresses_tab`|Tab that shows all wallet addresses.|
|`#contacts_tab` |Tab showing contacts.|
|`#invoices_tab` |Tab showing invoices.|
|`#console_tab`  |Tab containing the console.|
|`#plugins_area` |Scrolling area where plugins are listed.|
|`#chains_area`  |Scrolling area where chains are listed.|
|`QWidget[scrollArea=true]`|Generic scrolling area.|
|`#qr_window`    |Window that shows a QR code and address.|

### Miscellaneous

Other customizable objects that do not fit in the above tables are described here.

|Name           |Description|
|---------------|-----------|
|`#amount_edit` |Input line for amount in the "Send" tab.|
|`#fee_edit`    |Input line for tx fee in the "Send" tab.|

## Lite Window Styles

The stylesheet can also contain rules for the lite window.

### Lite Window Objects

|Name                   |Description|
|-----------------------|-----------|
|`#lite_window`          |The lite window.|
|`#lite_label_input`     |Transaction label input line.|
|`#lite_balance_label`   |Wallet balance|
|`#lite_address_input`   |Input line for transaction recipient.|
|`#lite_amount_input`    |Input line for a transaction amount.|
|`#lite_send_button`     |"Send" button.|
|`#lite_history`         |History list.|
|`#lite_receiving`       |Receiving widget.|
