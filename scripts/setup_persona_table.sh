#!/bin/bash

# AWS DynamoDB Persona Table Setup Script
# Creates PersonaTable and populates with 40 diverse persona records

set -e  # Exit on any error

echo "🚀 Starting DynamoDB Persona Table Setup..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# 1. Create the PersonaTable
echo "📋 Creating PersonaTable..."
aws dynamodb create-table \
    --table-name PersonaTable \
    --attribute-definitions AttributeName=persona_id,AttributeType=S \
    --key-schema AttributeName=persona_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-west-2

echo "⏳ Waiting for table to be active..."
aws dynamodb wait table-exists --table-name PersonaTable --region us-west-2

echo "✅ Table created successfully!"

# 2. Insert persona records in batches
echo "👥 Inserting 40 persona records..."

# Batch 1: Records 1-25
echo "📝 Inserting batch 1 (records 1-25)..."
aws dynamodb batch-write-item \
    --request-items '{
        "PersonaTable": [
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_001"}, "age": {"N": "34"}, "gender": {"S": "Female"}, "ethnicity": {"S": "South Asian"}, "national_origin": {"S": "India"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "High"}, "profession": {"S": "Engineer"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_002"}, "age": {"N": "28"}, "gender": {"S": "Male"}, "ethnicity": {"S": "African-American"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "Medium"}, "profession": {"S": "Teacher"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_003"}, "age": {"N": "45"}, "gender": {"S": "Female"}, "ethnicity": {"S": "White"}, "national_origin": {"S": "Germany"}, "country_of_residence": {"S": "Germany"}, "income_level": {"S": "High"}, "profession": {"S": "Physician"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_004"}, "age": {"N": "31"}, "gender": {"S": "Male"}, "ethnicity": {"S": "Asian"}, "national_origin": {"S": "Japan"}, "country_of_residence": {"S": "Japan"}, "income_level": {"S": "Medium"}, "profession": {"S": "Business"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_005"}, "age": {"N": "52"}, "gender": {"S": "Female"}, "ethnicity": {"S": "Hispanic"}, "national_origin": {"S": "Mexico"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "Medium"}, "profession": {"S": "Entrepreneur"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_006"}, "age": {"N": "29"}, "gender": {"S": "Male"}, "ethnicity": {"S": "White"}, "national_origin": {"S": "France"}, "country_of_residence": {"S": "France"}, "income_level": {"S": "Low"}, "profession": {"S": "Student"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_007"}, "age": {"N": "41"}, "gender": {"S": "Female"}, "ethnicity": {"S": "Asian"}, "national_origin": {"S": "China"}, "country_of_residence": {"S": "Canada"}, "income_level": {"S": "High"}, "profession": {"S": "Architect"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_008"}, "age": {"N": "36"}, "gender": {"S": "Male"}, "ethnicity": {"S": "South Asian"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "High"}, "profession": {"S": "Real Estate"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_009"}, "age": {"N": "58"}, "gender": {"S": "Female"}, "ethnicity": {"S": "African-American"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "Canada"}, "income_level": {"S": "Medium"}, "profession": {"S": "Journalist"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_010"}, "age": {"N": "25"}, "gender": {"S": "Male"}, "ethnicity": {"S": "Hispanic"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "Low"}, "profession": {"S": "Fitness Professional"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_011"}, "age": {"N": "67"}, "gender": {"S": "Female"}, "ethnicity": {"S": "White"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "High"}, "profession": {"S": "Physician"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_012"}, "age": {"N": "33"}, "gender": {"S": "Male"}, "ethnicity": {"S": "Asian"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "Medium"}, "profession": {"S": "Engineer"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_013"}, "age": {"N": "48"}, "gender": {"S": "Female"}, "ethnicity": {"S": "South Asian"}, "national_origin": {"S": "India"}, "country_of_residence": {"S": "Germany"}, "income_level": {"S": "High"}, "profession": {"S": "Business"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_014"}, "age": {"N": "22"}, "gender": {"S": "Male"}, "ethnicity": {"S": "White"}, "national_origin": {"S": "Germany"}, "country_of_residence": {"S": "Germany"}, "income_level": {"S": "Low"}, "profession": {"S": "Student"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_015"}, "age": {"N": "55"}, "gender": {"S": "Female"}, "ethnicity": {"S": "Hispanic"}, "national_origin": {"S": "Mexico"}, "country_of_residence": {"S": "Mexico"}, "income_level": {"S": "Medium"}, "profession": {"S": "Teacher"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_016"}, "age": {"N": "39"}, "gender": {"S": "Male"}, "ethnicity": {"S": "African-American"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "France"}, "income_level": {"S": "High"}, "profession": {"S": "Entrepreneur"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_017"}, "age": {"N": "44"}, "gender": {"S": "Female"}, "ethnicity": {"S": "Asian"}, "national_origin": {"S": "Japan"}, "country_of_residence": {"S": "Japan"}, "income_level": {"S": "Medium"}, "profession": {"S": "Architect"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_018"}, "age": {"N": "61"}, "gender": {"S": "Male"}, "ethnicity": {"S": "White"}, "national_origin": {"S": "France"}, "country_of_residence": {"S": "Canada"}, "income_level": {"S": "High"}, "profession": {"S": "Real Estate"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_019"}, "age": {"N": "27"}, "gender": {"S": "Female"}, "ethnicity": {"S": "South Asian"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "Medium"}, "profession": {"S": "Journalist"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_020"}, "age": {"N": "50"}, "gender": {"S": "Male"}, "ethnicity": {"S": "Hispanic"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "High"}, "profession": {"S": "Physician"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_021"}, "age": {"N": "35"}, "gender": {"S": "Female"}, "ethnicity": {"S": "White"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "Germany"}, "income_level": {"S": "Medium"}, "profession": {"S": "Fitness Professional"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_022"}, "age": {"N": "72"}, "gender": {"S": "Male"}, "ethnicity": {"S": "Asian"}, "national_origin": {"S": "China"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "Low"}, "profession": {"S": "Teacher"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_023"}, "age": {"N": "26"}, "gender": {"S": "Female"}, "ethnicity": {"S": "African-American"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "Low"}, "profession": {"S": "Student"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_024"}, "age": {"N": "43"}, "gender": {"S": "Male"}, "ethnicity": {"S": "South Asian"}, "national_origin": {"S": "India"}, "country_of_residence": {"S": "Canada"}, "income_level": {"S": "High"}, "profession": {"S": "Engineer"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_025"}, "age": {"N": "38"}, "gender": {"S": "Female"}, "ethnicity": {"S": "Hispanic"}, "national_origin": {"S": "Mexico"}, "country_of_residence": {"S": "France"}, "income_level": {"S": "Medium"}, "profession": {"S": "Business"}}}}
        ]
    }' \
    --region us-west-2

# Batch 2: Records 26-40
echo "📝 Inserting batch 2 (records 26-40)..."
aws dynamodb batch-write-item \
    --request-items '{
        "PersonaTable": [
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_026"}, "age": {"N": "54"}, "gender": {"S": "Male"}, "ethnicity": {"S": "White"}, "national_origin": {"S": "Germany"}, "country_of_residence": {"S": "France"}, "income_level": {"S": "High"}, "profession": {"S": "Architect"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_027"}, "age": {"N": "30"}, "gender": {"S": "Female"}, "ethnicity": {"S": "Asian"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "Japan"}, "income_level": {"S": "Medium"}, "profession": {"S": "Real Estate"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_028"}, "age": {"N": "47"}, "gender": {"S": "Male"}, "ethnicity": {"S": "African-American"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "Germany"}, "income_level": {"S": "Medium"}, "profession": {"S": "Journalist"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_029"}, "age": {"N": "65"}, "gender": {"S": "Female"}, "ethnicity": {"S": "South Asian"}, "national_origin": {"S": "India"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "High"}, "profession": {"S": "Physician"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_030"}, "age": {"N": "24"}, "gender": {"S": "Male"}, "ethnicity": {"S": "Hispanic"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "Mexico"}, "income_level": {"S": "Low"}, "profession": {"S": "Fitness Professional"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_031"}, "age": {"N": "59"}, "gender": {"S": "Female"}, "ethnicity": {"S": "White"}, "national_origin": {"S": "France"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "High"}, "profession": {"S": "Entrepreneur"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_032"}, "age": {"N": "32"}, "gender": {"S": "Male"}, "ethnicity": {"S": "Asian"}, "national_origin": {"S": "Japan"}, "country_of_residence": {"S": "Canada"}, "income_level": {"S": "Medium"}, "profession": {"S": "Teacher"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_033"}, "age": {"N": "46"}, "gender": {"S": "Female"}, "ethnicity": {"S": "African-American"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "Japan"}, "income_level": {"S": "High"}, "profession": {"S": "Business"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_034"}, "age": {"N": "21"}, "gender": {"S": "Male"}, "ethnicity": {"S": "South Asian"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "Germany"}, "income_level": {"S": "Low"}, "profession": {"S": "Student"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_035"}, "age": {"N": "63"}, "gender": {"S": "Female"}, "ethnicity": {"S": "Hispanic"}, "national_origin": {"S": "Mexico"}, "country_of_residence": {"S": "Canada"}, "income_level": {"S": "Medium"}, "profession": {"S": "Engineer"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_036"}, "age": {"N": "37"}, "gender": {"S": "Male"}, "ethnicity": {"S": "White"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "France"}, "income_level": {"S": "High"}, "profession": {"S": "Architect"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_037"}, "age": {"N": "51"}, "gender": {"S": "Female"}, "ethnicity": {"S": "Asian"}, "national_origin": {"S": "China"}, "country_of_residence": {"S": "Germany"}, "income_level": {"S": "Medium"}, "profession": {"S": "Real Estate"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_038"}, "age": {"N": "42"}, "gender": {"S": "Male"}, "ethnicity": {"S": "African-American"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "Mexico"}, "income_level": {"S": "Medium"}, "profession": {"S": "Journalist"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_039"}, "age": {"N": "75"}, "gender": {"S": "Female"}, "ethnicity": {"S": "South Asian"}, "national_origin": {"S": "India"}, "country_of_residence": {"S": "France"}, "income_level": {"S": "Low"}, "profession": {"S": "Teacher"}}}},
            {"PutRequest": {"Item": {"persona_id": {"S": "persona_040"}, "age": {"N": "49"}, "gender": {"S": "Male"}, "ethnicity": {"S": "Hispanic"}, "national_origin": {"S": "USA"}, "country_of_residence": {"S": "USA"}, "income_level": {"S": "High"}, "profession": {"S": "Fitness Professional"}}}}
        ]
    }' \
    --region us-west-2

echo "✅ All 40 persona records inserted successfully!"

# 3. Verify the records
echo "🔍 Verifying table contents..."
RECORD_COUNT=$(aws dynamodb scan --table-name PersonaTable --region us-west-2 --select COUNT --query 'Count' --output text)
echo "📊 Total records in table: $RECORD_COUNT"

if [ "$RECORD_COUNT" -eq 40 ]; then
    echo "🎉 SUCCESS: All 40 persona records created successfully!"
else
    echo "⚠️  WARNING: Expected 40 records, found $RECORD_COUNT"
fi

echo ""
echo "🏁 Script completed! PersonaTable is ready for use."
echo "📍 Table Name: PersonaTable"
echo "🌍 Region: us-west-2"
echo "💾 Records: $RECORD_COUNT personas"