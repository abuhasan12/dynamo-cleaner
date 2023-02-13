import boto3

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table1 = dynamodb.Table(event['table1'])
    table2 = dynamodb.Table(event['table2'])
    key = event['key']
    
    def get_all_items(table):
        items = []
        last_key = None
        while True:
            if last_key:
                response = table.scan(ExclusiveStartKey=last_key)
            else:
                response = table.scan()
            items += response['Items']
            last_key = response.get('LastEvaluatedKey', None)
            if last_key is None:
                break
        return items
    
    def add_missing_items(table1, table2):
        items1 = get_all_items(table1)
        items2 = get_all_items(table2)
        item_keys1 = set([item[key] for item in items1])
        for item in items2:
            if item[key] not in item_keys1:
                table1.put_item(Item=item)
    
    add_missing_items(table1, table2)