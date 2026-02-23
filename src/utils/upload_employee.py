"""
Script to upload employee CSV data to Azure Cosmos DB

This script reads employee data from a CSV file and uploads it to Azure Cosmos DB.
"""

import csv
import os
import sys
from typing import List, Dict
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class CosmosDBUploader:
    """Handle CSV to Cosmos DB upload operations."""
    
    def __init__(self):
        """Initialize Cosmos DB client and container."""
        # Get configuration from environment
        self.endpoint = os.getenv('COSMOS_DB_ENDPOINT')
        self.key = os.getenv('COSMOS_DB_KEY')
        self.database_name = os.getenv('COSMOS_DB_DATABASE_NAME')
        self.container_name = 'employees'  # Container for employee data
        
        # Validate configuration
        if not all([self.endpoint, self.key, self.database_name]):
            raise ValueError("Missing required Cosmos DB configuration in environment variables")
        
        # Initialize Cosmos client
        self.client = CosmosClient(self.endpoint, self.key)
        self.database = None
        self.container = None
        
        logger.info("Cosmos DB client initialized successfully")
    
    def setup_database_and_container(self):
        """Create database and container if they don't exist."""
        try:
            # Create or get database
            try:
                self.database = self.client.create_database(id=self.database_name)
                logger.info(f"Database '{self.database_name}' created successfully")
            except exceptions.CosmosResourceExistsError:
                self.database = self.client.get_database_client(self.database_name)
                logger.info(f"Database '{self.database_name}' already exists")
            
            # Create or get container
            try:
                # Try creating without throughput first (for serverless accounts)
                self.container = self.database.create_container(
                    id=self.container_name,
                    partition_key=PartitionKey(path="/Department")
                )
                logger.info(f"Container '{self.container_name}' created successfully (serverless mode)")
            except exceptions.CosmosHttpResponseError as e:
                # If it fails, try with throughput (for provisioned accounts)
                if "serverless" not in str(e).lower():
                    try:
                        self.container = self.database.create_container(
                            id=self.container_name,
                            partition_key=PartitionKey(path="/Department"),
                            offer_throughput=400
                        )
                        logger.info(f"Container '{self.container_name}' created successfully (provisioned mode)")
                    except exceptions.CosmosResourceExistsError:
                        self.container = self.database.get_container_client(self.container_name)
                        logger.info(f"Container '{self.container_name}' already exists")
                else:
                    raise
            except exceptions.CosmosResourceExistsError:
                self.container = self.database.get_container_client(self.container_name)
                logger.info(f"Container '{self.container_name}' already exists")
                
        except Exception as e:
            logger.error(f"Error setting up database/container: {str(e)}")
            raise
    
    def read_csv_file(self, csv_file_path: str) -> List[Dict]:
        """
        Read employee data from CSV file.
        
        Args:
            csv_file_path: Path to the CSV file
            
        Returns:
            List of employee dictionaries
        """
        employees = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Create employee document
                    employee = {
                        'id': row['Employee_ID'],  # Use Employee_ID as document id
                        'Name': row['Name'],
                        'Age': int(row['Age']),
                        'Employee_ID': row['Employee_ID'],
                        'Department': row['Department'],
                        'Date_of_Joining': row['Date_of_Joining'],
                        'Position': row['Position']
                    }
                    employees.append(employee)
            
            logger.info(f"Successfully read {len(employees)} employees from CSV file")
            return employees
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            raise
    
    def upload_employees(self, employees: List[Dict], batch_size: int = 10):
        """
        Upload employee data to Cosmos DB.
        
        Args:
            employees: List of employee dictionaries
            batch_size: Number of items to log progress after
        """
        if not self.container:
            raise ValueError("Container not initialized. Call setup_database_and_container() first")
        
        success_count = 0
        error_count = 0
        
        logger.info(f"Starting upload of {len(employees)} employees...")
        
        for idx, employee in enumerate(employees, 1):
            try:
                # Upsert employee document (insert or update if exists)
                self.container.upsert_item(body=employee)
                success_count += 1
                
                # Log progress
                if idx % batch_size == 0:
                    logger.info(f"Processed {idx}/{len(employees)} employees...")
                    
            except exceptions.CosmosHttpResponseError as e:
                error_count += 1
                logger.error(f"Error uploading employee {employee['Employee_ID']}: {str(e)}")
            except Exception as e:
                error_count += 1
                logger.error(f"Unexpected error uploading employee {employee['Employee_ID']}: {str(e)}")
        
        # Final summary
        logger.info("=" * 60)
        logger.info(f"Upload completed!")
        logger.info(f"Successfully uploaded: {success_count} employees")
        logger.info(f"Errors: {error_count} employees")
        logger.info("=" * 60)
        
        return success_count, error_count
    
    def verify_upload(self) -> int:
        """
        Verify the upload by counting documents in the container.
        
        Returns:
            Count of documents in container
        """
        if not self.container:
            raise ValueError("Container not initialized")
        
        try:
            # Query to count all documents
            query = "SELECT VALUE COUNT(1) FROM c"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            count = items[0] if items else 0
            logger.info(f"Total documents in container: {count}")
            return count
        except Exception as e:
            logger.error(f"Error verifying upload: {str(e)}")
            raise
    
    def query_sample_data(self, department: str = None, limit: int = 5):
        """
        Query and display sample employee data.
        
        Args:
            department: Filter by department (optional)
            limit: Number of records to display
        """
        if not self.container:
            raise ValueError("Container not initialized")
        
        try:
            if department:
                query = f"SELECT TOP {limit} * FROM c WHERE c.Department = @department"
                parameters = [{"name": "@department", "value": department}]
            else:
                query = f"SELECT TOP {limit} * FROM c"
                parameters = None
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"\nSample data ({len(items)} records):")
            logger.info("-" * 80)
            for item in items:
                logger.info(f"ID: {item['Employee_ID']}, Name: {item['Name']}, "
                          f"Department: {item['Department']}, Position: {item['Position']}")
            logger.info("-" * 80)
            
        except Exception as e:
            logger.error(f"Error querying sample data: {str(e)}")
            raise


def main():
    """Main execution function."""
    
    # CSV file path
    csv_file = r'C:\Users\suraj.vishwakarma\Downloads\employees_200.csv'
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        logger.error(f"CSV file '{csv_file}' not found in current directory")
        sys.exit(1)
    
    try:
        # Initialize uploader
        logger.info("Initializing Cosmos DB uploader...")
        uploader = CosmosDBUploader()
        
        # Setup database and container
        logger.info("Setting up database and container...")
        uploader.setup_database_and_container()
        
        # Read CSV file
        logger.info(f"Reading CSV file: {csv_file}")
        employees = uploader.read_csv_file(csv_file)
        
        # Upload to Cosmos DB
        logger.info("Uploading employees to Cosmos DB...")
        success, errors = uploader.upload_employees(employees)
        
        # Verify upload
        logger.info("\nVerifying upload...")
        total_count = uploader.verify_upload()
        
        # Display sample data
        logger.info("\nQuerying sample data...")
        uploader.query_sample_data(limit=5)
        
        # Display statistics by department
        logger.info("\nDisplaying statistics by department...")
        departments = set(emp['Department'] for emp in employees)
        for dept in sorted(departments):
            dept_employees = [emp for emp in employees if emp['Department'] == dept]
            logger.info(f"  {dept}: {len(dept_employees)} employees")
        
        logger.info("\n✅ CSV data successfully uploaded to Azure Cosmos DB!")
        
    except Exception as e:
        logger.error(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
