from webshop.webshop.shopping_cart import cart
from dt_ecommerce.api.shopping_cart import get_party
from erpnext.portal import utils as portal_utils

from dt_ecommerce.api.portal import create_customer_or_supplier

portal_utils.create_customer_or_supplier = create_customer_or_supplier
cart.get_party = get_party