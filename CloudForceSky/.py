import boto3
import json

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# --------------- Helper Functions ------------------

def index_faces(bucket, key):

    response = rekognition.index_faces(
        Image={"S3Object":
            {"Bucket": bucket,
            "Name": key}},
            CollectionId="face")
    return response
    
def update_index(tableName,faceId, fullName):
    response = dynamodb.put_item(
        TableName=tableName,
        Item={
            'RekognitionId': {'S': faceId},
            'FullName': {'S': fullName}
            }
        ) 


# --------------- Main handler ------------------

def lambda_handler(event, context):
  # Reference the bucket name explicitly
  bucket_name = "cloudsky"

  try:
    # Get the image from S3 (assuming key is retrieved from Records)
    key = event['Records'][0]['s3']['object']['key']
    image = s3.get_object(Bucket=bucket_name, Key=key)['Body'].read()

    # Send the image to Rekognition to detect faces
    response = rekognition.detect_faces(Image={'Bytes': image})

    # If faces are detected, populate DynamoDB and trigger SNS
    if response['FaceDetails']:
      table = dynamodb.Table('serverless-db')
      table.put_item(Item={
        'image_key': key,
        'face_detected': True
      })

      sns.publish(
        TopicArn='arn:aws:sns:us-east-1:298303098278:serverless',
        Message='Face detected in image: {}'.format(key)
      )

  except KeyError:
    # Handle the case where 'Records' key is missing
    print("Error: 'Records' key not found in event data")
    return {
      'statusCode': 400,
      'statusMessage': 'Error processing image'
    }

    # No faces detected, do something else (optional logic here)
  else:
        # No faces detected (assuming you want to do something here)
        pass
  

  return {
    'statusCode': 200,
    'statusMessage': 'Image processed successfully'
  }
