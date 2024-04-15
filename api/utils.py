from rest_framework.response import Response
from rest_framework import status
from biochatter_metta.prompts import BioCypherPromptEngine


# Check if the id exists in the database
def record_exists(record_model, record_id):
    return record_model.objects.filter(pk=record_id).exists()

# Update only the fields present in update_data
def update_record(record_instance, update_data):
    if record_instance:
        for key, value in update_data.items():
            setattr(record_instance, key, value)
        record_instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        return Response('Record does not exist!' ,status=status.HTTP_404_NOT_FOUND)

def get_records(filtered_records, record_serializer):
    serialized_records = record_serializer(filtered_records, many=True).data
    return Response(serialized_records, status=status.HTTP_200_OK)

def get_paginated_records(pagination_class, request, record_items, record_serializer_class):
    paginator = pagination_class()
    result_page = paginator.paginate_queryset(record_items, request)
    serialized_topics = record_serializer_class(result_page, many=True)
    return paginator.get_paginated_response(serialized_topics.data)

def add_record(record_data, record_model, record_serializer, additional_fields=None, get_serialized_record=False):
    if additional_fields is not None:
        record_data.update(additional_fields)
        # for key, value in additional_fields:
        #     if record_exists(record_model=record_model, record_id=)
    
    serialized_record = record_serializer(data=record_data)

    if serialized_record.is_valid():
        created_record = record_model.objects.create(**serialized_record.validated_data)
        serialized_record = record_serializer(created_record)

        #Incase we only want the serialized data
        if get_serialized_record:
            return serialized_record.data
        
        return Response(serialized_record.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serialized_record.errors, status=status.HTTP_400_BAD_REQUEST)
    
def add_message_record(user_data, chat_id, message_model, message_serializer_class, llm_context=''):
    prompt_engine = BioCypherPromptEngine(
            model_name='gpt-3.5-turbo',
            schema_config_or_info_path='./api/bio_data/biocypher_config/schema_config.yaml',
            schema_mappings='./api/bio_data/biocypher_config/schema_mappings.json',
            openai_api_key='*****'
        )

    user_message = user_data['message_text']
    try:
        metta_response = prompt_engine.get_metta_response(
            user_question=user_message,
            with_llm_response=True,
            llm_context=llm_context
            )

        if not metta_response['llm_response']:
            raise Exception('Unable to get LLM response!')
    except Exception as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    llm_message = {
        'message_text': metta_response['llm_response']
    }

    user_record = add_record(
        record_data = dict(user_data),
        record_model = message_model,
        record_serializer= message_serializer_class,
        additional_fields={'chat_id': chat_id},
        get_serialized_record=True
    )

    llm_record = add_record(
        record_data = llm_message,
        record_model = message_model,
        record_serializer= message_serializer_class,
        additional_fields={'chat_id': chat_id, 'is_user_message': False},
        get_serialized_record=True
    )

    return user_record, llm_record