# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from unittest import TestCase

from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres")


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should read a product in database """

        # Creation of the product
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        # Found the product and check infos
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should update a product"""

        # Creation of the product
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        # Make the update and check the changement as became
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")

        # Make sure ain't no change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_update_with_empty_id(self):
        """It should raise DataValidationError when update is called with an empty ID"""

        # Create a product instance with an empty ID
        product = Product(id=None, name="Test Product", description="Description", price=10.99, available=True, category="CATEGORY")

        # Attempt to call update and assert that it raises DataValidationError
        with self.assertRaises(DataValidationError):
            product.update()

    def test_delete_a_product(self):
        """It should delete a product"""

        # Creation of the product
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        self.assertEqual(len(Product.all()), 1)

        # Delete and check the product doesn't exist anymore
        product.delete()
        self.assertEqual(len(Product.all()), 0)

        # Try to retrieve the deleted product
        with self.assertRaises(AttributeError):
            Product.find_by_id(product.id)

    def test_list_all_products(self):
        """It should list all products in the database"""

        # There is no product in database
        products = Product.all()
        self.assertEqual(products, [])

        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()

        # Check if we have been have 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should find a product by name"""

        # Create 5 products with unique names
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()

        # Select a name to target
        target_name = products[0].name
        expected_count = len([product for product in products if product.name == target_name])

        # Find the products by name
        found_products_query = Product.find_by_name(target_name)
        found_products = found_products_query.all()

        # Assert the products  searched are all found
        self.assertEqual(len(found_products), expected_count)
        for product in found_products:
            self.assertEqual(product.name, target_name)

    def test_find_by_availability(self):
        """It should find products by availability"""

        # Create 3 products available and 3 other's not
        availability = True
        available_products = ProductFactory.create_batch(3, available=availability)
        unavailable_products = ProductFactory.create_batch(3, available=not availability)

        # Create all products in the database
        for product in available_products + unavailable_products:
            product.create()

        # Find products by availability using the method
        found_products_query = Product.find_by_availability(availability)
        found_products = found_products_query.all()

        # Assert the available products are all found
        self.assertEqual(len(found_products), len(available_products))
        for product in found_products:
            self.assertEqual(product.available, availability)

    def test_find_by_category(self):
        """It should find products by category"""

        # Create 10 products
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()

        # Get the category of the first product
        category = products[0].category

        # Count the number of products with the specified category
        count = len([product for product in products if product.category == category])

        # Find products by category using the method
        found_products_query = Product.find_by_category(category)
        found_products = found_products_query.all()

        # Assert the in the category searched are found
        self.assertEqual(len(found_products), count)
        for product in found_products:
            self.assertEqual(product.category, category)

    def test_find_by_price(self):
        """It should return all Products with the given price"""

        # Create 10 products
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()

        # Get the price of the first product
        price = products[0].price

        # Count the number of products with the specified price
        count = len([product for product in products if product.price == price])

        # Find products by price using the method
        found_products_query = Product.find_by_price(price)
        found_products = found_products_query.all()

        # Assert the in the price searched are found
        self.assertEqual(len(found_products), count)
        for product in found_products:
            self.assertEqual(product.price, price)

    def test_deserialize_valid_data(self):
        """It should deserialize valid data without raising errors"""

        # Create a product instance and provide valid data
        valid_data = {
            "name": "Test Product",
            "description": "Description",
            "price": "10.99",
            "available": True,
            "category": "UNKNOWN"  # Use a valid enum value
        }
        product = ProductFactory()
        product.deserialize(valid_data)

        # Assert that the deserialization was successful
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.description, "Description")
        self.assertEqual(product.price, Decimal("10.99"))
        self.assertTrue(product.available)
        self.assertEqual(product.category, Category.UNKNOWN)

    def test_deserialize_invalid_decimal_value(self):
        """It should raise DataValidationError for invalid available state"""

        # Create a product instance and provide data with an invalid decimal value
        invalid_data = {
            "name": "Test Product",
            "description": "Description",
            "price": 2,
            "available": 2015, # not a boolean
            "category": "UNKNOWN"
        }

        # Attempt to deserialize and assert that it raises DataValidationError
        product = ProductFactory()
        with self.assertRaises(DataValidationError):
            product.deserialize(invalid_data)

    def test_deserialize_invalid_enum_value(self):
        """It should raise DataValidationError for invalid enum value in data"""

        # Create a product instance and provide data with an invalid enum value
        invalid_data = {
            "name": "Test Product",
            "description": "Description",
            "price": "10.99",
            "available": True,
            "category": "INVALID_CATEGORY"  # Invalid enum value
        }

        # Attempt to deserialize and assert that it raises DataValidationError
        product = ProductFactory()
        with self.assertRaises(DataValidationError):
            product.deserialize(invalid_data)
