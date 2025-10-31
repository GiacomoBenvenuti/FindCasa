#!/usr/bin/env python3
"""
Comprehensive test suite for RMVScraper class methods.

This test suite uses actual HTML files from Rightmove to test all methods
of the RMVScraper class:
- test_page.html: Contains a search results page with multiple property cards
- listing_card.html: Contains a single property detail page with
  window.PAGE_MODEL
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import requests

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import RMVScraper


class TestRMVScraperMethods(unittest.TestCase):
    """Test suite for RMVScraper class methods using real HTML data."""
    
    def setUp(self):
        """Set up test environment with scraper instance and test data."""
        self.scraper = RMVScraper()
        self.test_dir = tempfile.mkdtemp()
        
        # Test file paths - use relative paths for both dev container and CI
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_page_path = os.path.join(
            script_dir, "test", "test_page.html")
        self.listing_card_path = os.path.join(
            script_dir, "test", "listing_card.html")
        
        # Verify test files exist
        self.assertTrue(os.path.exists(self.test_page_path),
                        "test_page.html should exist in test directory")
        self.assertTrue(os.path.exists(self.listing_card_path),
                        "listing_card.html should exist in test directory")
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_init_configuration(self):
        """Test that RMVScraper initializes correctly with configuration."""
        # Test that scraper has required attributes
        self.assertIsNotNone(self.scraper.config)
        self.assertIsNotNone(self.scraper.proxies)
        self.assertIsNotNone(self.scraper.headers)
        
        # Test that User-Agent is set
        self.assertIn("User-Agent", self.scraper.headers)
        self.assertIsNotNone(self.scraper.headers["User-Agent"])
        
        # Test that session is initially None
        self.assertIsNone(self.scraper.session)
    
    def test_setup_session(self):
        """Test that _setup_session creates a proper requests session."""
        # Call _setup_session
        self.scraper._setup_session()
        
        # Verify session was created
        self.assertIsNotNone(self.scraper.session)
        self.assertIsInstance(self.scraper.session, requests.Session)
        
        # Verify headers are applied
        self.assertEqual(self.scraper.session.headers["User-Agent"],
                         self.scraper.headers["User-Agent"])
        
        # Verify proxies are applied
        self.assertEqual(self.scraper.session.proxies, self.scraper.proxies)
    
    @patch('main.requests.Session')
    def test_download_page_success(self, mock_session_class):
        """Test download_page method with successful response."""
        # Set up mock session and response
        mock_session = MagicMock()
        self.scraper.session = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        
        # Test successful download
        result = self.scraper.download_page("http://test.com", 30)
        
        # Verify response is returned
        self.assertEqual(result, mock_response)
        
        # Verify session.get was called with correct parameters
        mock_session.get.assert_called_once_with(
            "http://test.com",
            proxies=self.scraper.proxies,
            headers=self.scraper.headers,
            timeout=30
        )
    
    @patch('main.requests.Session')
    def test_download_page_failure(self, mock_session_class):
        """Test download_page method with failed response."""
        # Set up mock session and response
        mock_session = MagicMock()
        self.scraper.session = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response
        
        # Test failed download
        result = self.scraper.download_page("http://test.com", 30)
        
        # Verify None is returned for failed response
        self.assertIsNone(result)
    
    @patch('main.requests.Session')
    def test_download_page_exception(self, mock_session_class):
        """Test download_page method with exception."""
        # Set up mock session to raise exception
        mock_session = MagicMock()
        self.scraper.session = mock_session
        mock_session.get.side_effect = requests.exceptions.Timeout("Timeout")
        
        # Test exception handling
        result = self.scraper.download_page("http://test.com", 30)
        
        # Verify None is returned for exception
        self.assertIsNone(result)
    
    @patch('main.sleep')
    def test_download_property_page(self, mock_sleep):
        """Test download_property_page method."""
        # Mock the download_page method
        with patch.object(self.scraper, 'download_page') as mock_download:
            mock_response = MagicMock()
            mock_download.return_value = mock_response
            
            # Set up session (required for header/proxy updates)
            self.scraper._setup_session()
            
            # Test download_property_page
            result = self.scraper.download_property_page(
                "http://test.com", 30, 1.0, 3.0)
            
            # Verify sleep was called with delay in range
            mock_sleep.assert_called_once()
            delay_arg = mock_sleep.call_args[0][0]
            self.assertGreaterEqual(delay_arg, 1.0)
            self.assertLessEqual(delay_arg, 3.0)
            
            # Verify download_page was called
            mock_download.assert_called_once_with("http://test.com", 30)
            
            # Verify result is returned
            self.assertEqual(result, mock_response)
    
    def test_extract_listing_data_with_real_html(self):
        """Test extract_listing_data method with real Rightmove HTML."""
        # Read the test HTML file
        with open(self.test_page_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Create a mock response object
        mock_response = MagicMock()
        mock_response.text = html_content
        
        # Test extraction
        listings = self.scraper.extract_listing_data(mock_response)
        
        # Verify listings were found
        self.assertIsInstance(listings, list)
        self.assertGreater(len(listings), 0, "Should find property listings")
        
        # Verify each listing is a BeautifulSoup element
        for listing in listings:
            self.assertIsNotNone(listing)
            # Check if it has the expected CSS class
            classes = listing.get('class', [])
            self.assertIn('PropertyCard_propertyCardContainerWrapper__mcK1Z', 
                         classes)
    
    def test_parse_property_json_with_real_html(self):
        """Test _parse_property_json method with real property HTML."""
        # Read the listing card HTML file
        with open(self.listing_card_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Test JSON parsing
        property_data = self.scraper._parse_property_json(html_content)
        
        # Verify property data was extracted
        self.assertIsNotNone(property_data, "Should extract property data")
        self.assertIsInstance(property_data, dict)
        
        # Verify required structure
        self.assertIn('propertyData', property_data)
        self.assertIn('id', property_data['propertyData'])
        
        # Verify property ID is correct (from the listing_card.html)
        property_id = property_data['propertyData']['id']
        self.assertEqual(property_id, "165672272")
        
        # Verify other expected fields
        self.assertIn('status', property_data['propertyData'])
        self.assertIn('published', property_data['propertyData']['status'])
    
    def test_parse_property_json_no_script_tag(self):
        """Test _parse_property_json with HTML that has no PAGE_MODEL."""
        # HTML without window.PAGE_MODEL
        html_content = """
        <html>
        <head><title>Test</title></head>
        <body>
            <script>var someOtherVar = 'test';</script>
        </body>
        </html>
        """
        
        # Test parsing should return None
        result = self.scraper._parse_property_json(html_content)
        self.assertIsNone(result)
    
    def test_parse_property_json_invalid_json(self):
        """Test _parse_property_json with invalid JSON data."""
        # HTML with malformed JSON
        html_content = """
        <html>
        <script>
        window.PAGE_MODEL = { invalid json here }
        </script>
        </html>
        """
        
        # Test parsing should return None due to invalid JSON
        result = self.scraper._parse_property_json(html_content)
        self.assertIsNone(result)
    
    def test_save_property_data(self):
        """Test _save_property_data method."""
        # Sample property data
        property_data = {
            'propertyData': {
                'id': '123456789',
                'status': {'published': True, 'archived': False},
                'address': {'displayAddress': 'Test Street, Cambridge'},
                'prices': {'primaryPrice': 500000}
            }
        }
        
        # Change to test directory and create data subdirectory
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        os.makedirs('data', exist_ok=True)
        
        try:
            # Test saving
            result = self.scraper._save_property_data(property_data)
            
            # Verify save was successful
            self.assertTrue(result)
            
            # Verify file was created
            expected_filename = "data/id123456789.json"
            self.assertTrue(os.path.exists(expected_filename))
            
            # Verify file content
            with open(expected_filename, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data, property_data)
            
            # Test saving same file again (should skip)
            result2 = self.scraper._save_property_data(property_data)
            self.assertFalse(result2, "Should skip existing file")
            
        finally:
            os.chdir(original_cwd)
    
    def test_process_property_card_integration(self):
        """Test _process_property_card method with mocked dependencies."""
        # Create a mock property card from the real HTML
        with open(self.test_page_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find the first property card
        card = soup.find('div', class_='PropertyCard_propertyCardContainerWrapper__mcK1Z')
        self.assertIsNotNone(card, "Should find a property card in test HTML")
        
        # Mock the download and parsing methods
        with patch.object(self.scraper, 'download_property_page') as mock_download, \
             patch.object(self.scraper, '_parse_property_json') as mock_parse, \
             patch.object(self.scraper, '_save_property_data') as mock_save:
            
            # Set up mock returns
            mock_response = MagicMock()
            mock_response.text = "mock html content"
            mock_download.return_value = mock_response
            
            mock_property_data = {'propertyData': {'id': '123456'}}
            mock_parse.return_value = mock_property_data
            
            mock_save.return_value = True
            
            # Test processing
            result = self.scraper._process_property_card(
                card, 1.0, 2.0, 30)
            
            # Verify methods were called
            mock_download.assert_called_once()
            mock_parse.assert_called_once_with("mock html content")
            mock_save.assert_called_once_with(mock_property_data)
            
            # Verify success
            self.assertTrue(result)
    
    def test_process_property_card_no_link(self):
        """Test _process_property_card with card that has no property link."""
        # Create a mock card without the expected link
        html = """
        <div class="PropertyCard_propertyCardContainerWrapper__mcK1Z">
            <div>No property link here</div>
        </div>
        """
        soup = BeautifulSoup(html, 'html.parser')
        card = soup.find('div')
        
        # Test should handle missing link gracefully
        result = self.scraper._process_property_card(card, 1.0, 2.0, 30)
        self.assertFalse(result)
    
    @patch('main.sleep')
    def test_scrape_method_flow(self, mock_sleep):
        """Test the main scrape method flow with mocked dependencies."""
        # Mock all the HTTP requests and processing
        with patch.object(self.scraper, '_setup_session') as mock_setup, \
             patch.object(self.scraper, 'download_page') as mock_download, \
             patch.object(self.scraper, 'extract_listing_data') as mock_extract, \
             patch.object(self.scraper, '_process_property_card') as mock_process:
            
            # Set up mock returns
            mock_response = MagicMock()
            mock_download.return_value = mock_response
            
            # Mock listings - return empty list after first page to end loop
            mock_extract.side_effect = [
                [MagicMock(), MagicMock()],  # First page: 2 listings
                []  # Second page: no listings (end loop)
            ]
            
            mock_process.return_value = True
            
            # Test scraping
            result = self.scraper.scrape("http://test.com/search", delay=0.1)
            
            # Verify setup was called
            mock_setup.assert_called_once()
            
            # Verify download was called (at least once)
            self.assertGreater(mock_download.call_count, 0)
            
            # Verify extract was called
            self.assertGreater(mock_extract.call_count, 0)
            
            # Verify process was called for each listing
            self.assertEqual(mock_process.call_count, 2)
            
            # Verify return value
            self.assertIsInstance(result, list)
    
    def test_scrape_no_listings_found(self):
        """Test scrape method when no listings are found."""
        with patch.object(self.scraper, '_setup_session'), \
             patch.object(self.scraper, 'download_page') as mock_download, \
             patch.object(self.scraper, 'extract_listing_data') as mock_extract:
            
            mock_response = MagicMock()
            mock_download.return_value = mock_response
            mock_extract.return_value = []  # No listings found
            
            # Test scraping with no results
            result = self.scraper.scrape("http://test.com/search")
            
            # Should return empty list
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 0)
    
    def test_scrape_download_fails(self):
        """Test scrape method when download fails."""
        with patch.object(self.scraper, '_setup_session'), \
             patch.object(self.scraper, 'download_page') as mock_download:
            
            mock_download.return_value = None  # Download fails
            
            # Test scraping with failed download
            result = self.scraper.scrape("http://test.com/search")
            
            # Should return empty list
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 0)
    
    def test_configuration_integration(self):
        """Test that scraper correctly uses YAML configuration."""
        # Test that configuration values are loaded correctly
        config = self.scraper.config
        
        # Test CSS selectors
        container_selector = config.get('selectors.property_cards.container')
        self.assertIsNotNone(container_selector)
        self.assertIn('PropertyCard_propertyCardContainerWrapper', container_selector)
        
        # Test URL patterns
        base_url = config.get('website.base_url')
        self.assertIsNotNone(base_url)
        self.assertIn('rightmove.co.uk', base_url)
        
        # Test request settings
        timeout = config.get('request_settings.timeouts.page_request')
        self.assertIsNotNone(timeout)
        self.assertIsInstance(timeout, (int, float))
        
        # Test regex patterns
        regex_pattern = config.get('regex_patterns.page_model.pattern')
        self.assertIsNotNone(regex_pattern)
        self.assertIn('PAGE_MODEL', regex_pattern)


class TestRMVScraperWithRealData(unittest.TestCase):
    """Integration tests using real HTML data."""
    
    def setUp(self):
        """Set up test environment."""
        self.scraper = RMVScraper()
    
    def test_end_to_end_listing_extraction(self):
        """Test complete listing extraction pipeline with real HTML."""
        # Read the test page HTML
        script_dir = os.path.dirname(os.path.abspath(__file__))
        test_page_path = os.path.join(script_dir, "test", "test_page.html")
        with open(test_page_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.text = html_content
        
        # Extract listings
        listings = self.scraper.extract_listing_data(mock_response)
        
        # Verify we found actual property listings
        self.assertGreater(len(listings), 0)
        print(f"✓ Found {len(listings)} property listings in test HTML")
        
        # Test that we can find property links in the listings
        links_found = 0
        for listing in listings:
            link_selector = 'selectors.property_links.class'
            link_class = self.scraper.config.get(link_selector)
            property_link = listing.find('a', class_=link_class)
            if property_link and property_link.get('href'):
                links_found += 1
        
        print(f"✓ Found {links_found} property links in listings")
        self.assertGreater(links_found, 0, "Should find property links")
    
    def test_end_to_end_json_parsing(self):
        """Test complete JSON parsing with real property HTML."""
        # Read the listing card HTML
        script_dir = os.path.dirname(os.path.abspath(__file__))
        listing_card_path = os.path.join(
            script_dir, "test", "listing_card.html")
        with open(listing_card_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse the property data
        property_data = self.scraper._parse_property_json(html_content)
        
        # Verify successful parsing
        self.assertIsNotNone(property_data)
        print("✓ Successfully parsed property data")
        
        # Verify structure and content
        self.assertIn('propertyData', property_data)
        prop_data = property_data['propertyData']
        
        # Check key fields
        self.assertIn('id', prop_data)
        self.assertIn('status', prop_data)
        self.assertIn('prices', prop_data)
        
        print(f"✓ Property ID: {prop_data['id']}")
        print(f"✓ Property status: {prop_data['status']}")
        
        # Verify the property has expected data types
        self.assertIsInstance(prop_data['id'], str)
        self.assertIsInstance(prop_data['status'], dict)


def run_tests():
    """Run all tests with detailed output."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRMVScraperMethods))
    suite.addTests(loader.loadTestsFromTestCase(TestRMVScraperWithRealData))
    
    # Run tests with high verbosity
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 70)
    print("RMV SCRAPER COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("Testing all methods of RMVScraper class with real HTML data")
    print("Test files: test_page.html (search results) and")
    print("listing_card.html (property detail)")
    print()
    
    success = run_tests()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("RMVScraper class methods are working correctly with real HTML")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Check the output above for details")
    print("=" * 70)
    
    sys.exit(0 if success else 1)