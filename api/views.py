from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .models import *
from .serializers import *
from .utils import *

import json, os
from datetime import datetime
from biochatter_metta.prompts import get_llm_response
from biochatter_metta.metta_prompt import get_schema_items
# =========================================================== CHAT ===========================================================

class ChatList(APIView):
    def get(self, request):
        chats = Chat.objects.all()
        return get_paginated_records(
            pagination_class=LimitOffsetPagination,
            request=request,
            record_items=chats,
            record_serializer_class=ChatSerializer
        )
    
    def post(self, request):
        message_text = request.data.get('message_text', '')
        if not message_text:
            return Response('message_text is missing!', status=status.HTTP_400_BAD_REQUEST)

        llm_response, _, _ = get_llm_response(
            openai_api_key='*',
            prompt=f'''\
            Write a short and descriptive chat title based on the sample message below:
            "{message_text}"\
            The title should not me more than fifty characters long.\
            Return only the title and without any explanations.\
            '''.strip()
        )

        chat_record = add_record(
            record_data = {'chat_name': llm_response},
            record_model = Chat,
            record_serializer= ChatSerializer,
            get_serialized_record=True
        )
        chat_id = chat_record['id']

        # user_record, llm_record = add_message_record(
        #     user_data=request.data,
        #     chat_id=chat_id,
        #     message_model=Message,
        #     message_serializer_class=MessageSerializer
        # )

        return Response({
            'chat_record': chat_record,
            # 'user_record': user_record,
            # 'llm_record': llm_record
        }, status=status.HTTP_201_CREATED)

class ChatDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()

    def update(self, request, pk):
        chat_instance = Chat.objects.get(pk=pk)
        request.data.update({'chat_updated_at': datetime.now()})
        return update_record(
            record_instance = chat_instance,
            update_data = request.data
        )

# =========================================================== MESSAGE ===========================================================

class MessageList(APIView):
    def get(self, request, chat_id):
        chat_exists = record_exists(record_model=Chat, record_id=chat_id)
        if not chat_exists:
            return Response('Invalid Chat ID!' ,status=status.HTTP_400_BAD_REQUEST)
        
        messages = Message.objects.filter(chat_id=chat_id).order_by('-message_created_at')

        # /api/chats/<chat_id>/messages/?limit=2&offset=2 (Limit = no. of messages, Offset = start from)
        return get_paginated_records(
            pagination_class=LimitOffsetPagination,
            request=request,
            record_items=messages,
            record_serializer_class=MessageSerializer
        )
    
    def post(self, request, chat_id):
        chat_exists = record_exists(record_model=Chat, record_id=chat_id)
        if not chat_exists:
            return Response('Invalid Chat ID!' ,status=status.HTTP_400_BAD_REQUEST)

        # Get context length from query parameter
        context_length = self.request.query_params.get('context_length', 20)
        message_history = MessageSerializer( Message.objects.filter(chat_id=chat_id).order_by('-message_created_at')[:context_length], many=True ).data
        # Get the list in ascending chronological order
        message_history.reverse()
        # Format in chat style message
        llm_context = 'Use this interaction history between the "User" and the "Assistant" as additional context.\n\n ###\n'
        for message in message_history:
            smn = 'User' if message['is_user_message'] else 'Assistant'
            llm_context += f"{smn}: {message['message_text']}\n"
        llm_context += '\n###\n\n'

        user_record, llm_record = add_message_record(
            user_data=request.data,
            chat_id=chat_id,
            message_model=Message,
            message_serializer_class=MessageSerializer,
            llm_context=llm_context
        )

        # TODO: check both responses and return a single response
        return Response({
            'user_question': user_record,
            'llm_response': llm_record
        }, status=status.HTTP_201_CREATED)

class MessageDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

    def update(self, request, pk):
        message_instance = Message.objects.get(pk=pk)
        request.data.update({'message_updated_at': datetime.now()})
        return update_record(
            record_instance = message_instance,
            update_data = request.data
        )

# =========================================================== EXAMPLE ===========================================================

class ExampleList(APIView):
    def get(self, request):
        examples = Example.objects.all()

        return get_paginated_records(
            pagination_class=LimitOffsetPagination,
            request=request,
            record_items=examples,
            record_serializer_class=ExampleSerializer
        )

    def post(self, request):
        return add_record(
            record_data = dict(request.data),
            record_model = Example,
            record_serializer= ExampleSerializer
        )       

class ExampleDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExampleSerializer
    queryset = Example.objects.all()

    def update(self, request, pk):
        example_instance = Example.objects.get(pk=pk)
        
        return update_record(
            record_instance = example_instance,
            update_data = request.data
        )

# =========================================================== SCHEMA ===========================================================

class SchemaList(APIView):
    # serializer_class = SchemaSerializer
    # queryset = Schema.objects.all()
    # TODO: Adding a new schema should delete all the previous ones (including the Atomspaces)
    def get(self, request):
        # TODO: get a list of all the nodes & edges in the schema
            # - get the last schema file uploaded
            # - call a function from biochatter-metta that takes the .yaml path and lists all the entities
        # List all the entities' names and types
        # List any previously recorded file paths for the entities (if any)
        # {
        #     'type': 'node'
        #     'name': 'gene'
        #     'path': '/api/bio_data/bioatomspace/gene/_node_2556.metta
        # }
        schema = SchemaSerializer( Schema.objects.last() )
        schema_file_path = schema.data.get('schema_file', None)

        # if (schema_file_path is None) or (not os.path.isfile(schema_file_path)):
        #     return Response('Schema not found!', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        items = get_schema_items(f'./{schema_file_path}')

        nodes = []
        for node in items['nodes'].keys():
            nodes.append(node)
        edges = []
        for edge in items['edges'].keys():
            edges.append(edge)

        return Response({
            'nodes': nodes,
            'edges': edges
        }, status=status.HTTP_200_OK)

    def post(self, request):
        # Get the old schema path
        prev_schema_exists = Schema.objects.exists()
        if prev_schema_exists:
            prev_schema = Schema.objects.get(schema_name='Schema') or None
            prev_schema_path = os.path.abspath(prev_schema.schema_file.path) if prev_schema.schema_file else None

        schema, created = Schema.objects.update_or_create(
            defaults={'schema_file': request.FILES['schema_file']}
        )

        # Delete the old schema if the old one was updated
        if not created and prev_schema_exists: # Schema is updated
            if prev_schema_path and os.path.isfile(prev_schema_path):
                os.remove(prev_schema_path)

        # Write to schema_mappings
        serialized_schema = SchemaSerializer(schema).data
        schema_file_path = serialized_schema.get('schema_file', None)
        items = get_schema_items(f'./{schema_file_path}')

        with open('api/bio_data/schema_mappings.json', 'w') as f:
            json.dump(items, f)

        update_schema_mappings()

        return Response(f"Schema {'Uploaded' if created else 'Updated'}!",
                        status=status.HTTP_201_CREATED)
    
    def delete(self, request):
        if Schema.objects.exists():
            schema = Schema.objects.get(schema_name='Schema')

            schema.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

# =========================================================== ATOMSPACE ===========================================================

class AtomspaceList(generics.ListCreateAPIView):
    serializer_class = AtomspaceSerializer
    queryset = Atomspace.objects.all()

    def create(self, request):
        db_name = request.data.get('db_name', None)
        if db_name is None: 
            return Response('\'db_name\' filed is required.', status=status.HTTP_400_BAD_REQUEST)

        try:
            atomspace, created = Atomspace.objects.update_or_create(
                db_name=db_name,
                defaults={
                    'nodes': request.data.get('nodes', None),
                    'edges': request.data.get('edges', None),
                    'node_metta_file': request.FILES.get('node_metta_file', None),
                    'edge_metta_file': request.FILES.get('edge_metta_file', None)
                }
            )
            serialized_atomspace = AtomspaceSerializer(atomspace).data
            # serializer = AtomspaceSerializer(data=request.data)
            # if serializer.is_valid():
            #     atomspace_record = Atomspace.objects.create(**serializer.validated_data)
            #     serialized_record = AtomspaceSerializer(atomspace_record).data
            #     serializer.save()
            # else:
            #     return Response(serializer.error_messages, status=status.HTTP_400_BAD_REQUEST)
                
            # atomspace_record = serialized_record.data

            update_schema_mappings(atomspace_record=serialized_atomspace)

        except Exception as e:
            return Response(f'Error: {e}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # entity_type = atomspace_record['entity_type']
        # entity_names = ast.literal_eval(atomspace_record['entity_name'])

        # with open("api/api/bio_data/schema_mappings.json", "r+") as jsonFile:
        #     schema = json.load(jsonFile)
        #     for entity_name in entity_names:
        #         schema[f'{entity_type}s'][entity_name]['metta_location'] = atomspace_record['metta_file']

        #     jsonFile.seek(0)  # rewind cursor to beginning of file
        #     json.dump(schema, jsonFile)
        #     jsonFile.truncate() # delete any trailing data (if new content is shorter)

        return Response(serialized_atomspace, status=status.HTTP_204_NO_CONTENT)
    # db_name = models.CharField(max_length=100)
    # entity_name = models.CharField(max_length=100)
    # entity_type = models.CharField(max_length=10)
    # metta_file = models.FileField(upload_to=metta_file_path)
    # ['gene','transcript']
    # ['transcribed_to','transcribed_from']

class AtomspaceDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AtomspaceSerializer
    queryset = Atomspace.objects.all()

    