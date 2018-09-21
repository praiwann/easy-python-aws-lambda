FROM lambci/lambda:build-python3.6

ENV AWS_DEFAULT_REGION ap-southeast-1

CMD echo "compressing package from folder $PWD" && \
    cat lambdaignore | xargs zip -9qyr $COMPRESS_FILE_NAME.zip . -x && \
    echo "done compress package..." && \
    echo "uploading file to AWS S3 Bucket" && \
    aws s3 cp $COMPRESS_FILE_NAME.zip s3://$AWS_S3_LAMBDA_BUCKET/lambda/$COMPRESS_FILE_NAME.zip && \
    echo "updating lambda_function with file from S3 Bucket -> LAMBDA_FUNCTION_NAME: $LAMBDA_FUNCTION_NAME" && \
    aws lambda update-function-code --function-name $LAMBDA_FUNCTION_NAME \
    --s3-bucket $AWS_S3_LAMBDA_BUCKET --s3-key lambda/$COMPRESS_FILE_NAME.zip && \
    echo "done upload file..." && \
    echo "changing Lambda config of LAMBDA_FUNCTION_NAME: $LAMBDA_FUNCTION_NAME with HANDLER: $LAMBDA_MODULE" && \
    aws lambda update-function-configuration --function-name $LAMBDA_FUNCTION_NAME --handler $LAMBDA_MODULE && \
    echo tasks done...