# dt_ecommerce/install.py

from dt_ecommerce.setup.custom_fields import setup_storefront_custom_fields


def after_install():
    setup_storefront_custom_fields()