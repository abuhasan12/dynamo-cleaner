import json
import time
import boto3

def lambda_handler(event, context):
    dynamodb = boto3.client('dynamodb')
    
    # Get the keys from the event
    body = json.loads(event['body'])
    table_names = [s.strip() for s in body['tableNames'].split(',')]
    attribute_names = [s.strip() for s in body['attributeNames'].split(',')]
    attribute_types = [s.strip() for s in body['attributeTypes'].split(',')]
    attribute_values = [s.strip() for s in body['attributeValues'].split(',')]
    
    # Create expression attribute values
    expression_attribute_values = {}
    for idx, attribute_name in enumerate(attribute_names):
        attribute_name = ":" + attribute_name
        expression_attribute_values[attribute_name] = {attribute_types[idx]:attribute_values[idx]}
    
    # Create filter expression
    filter_expression = ""
    for i,key in enumerate(expression_attribute_values):
        filter_expression += key[1:]
        filter_expression += " = "
        filter_expression += key
        if i != len(expression_attribute_values) - 1:
            filter_expression += ' or '
        
    for table in table_names:
        table_name = table.strip()
        
        # Get key schema
        table_response = dynamodb.describe_table(
            TableName=table_name,
        )
        key_schema = table_response['Table']['KeySchema']
    
        # Store a full backup of the table before deletion
        backup_name = f"{table_name}-{int(time.time())}"
        backup_response = dynamodb.create_backup(
            TableName=table_name,
            BackupName=backup_name
        )
        
        # Attributes to paginate through scans
        has_more_data = True
        last_evaluated_key = None
        
        
        # Start scanning
        while has_more_data:
            if last_evaluated_key:
                response = dynamodb.scan(
                    TableName=table_name,
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_attribute_values,
                    ExclusiveStartKey=last_evaluated_key
                )
            else:
                response = dynamodb.scan(
                    TableName=table_name,
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )
            
            # Get matching and delete items
            items = response.get('Items', [])
            for item in items:
                item_key = {}
                for field in key_schema:
                    item_key[field['AttributeName']] = item[field['AttributeName']]
                dynamodb.delete_item(
                    TableName=table_name,
                    Key=item_key
                )
                
            # Update pagination attributes
            last_evaluated_key = response.get('LastEvaluatedKey', None)
            has_more_data = last_evaluated_key is not None
        
    return {
        'statusCode': 200,
        'headers': {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, x-api-key',
        },
        'body': json.dumps({'message': "Successfully deleted items and stored in backup."})
    }