from django.urls import path
from .views import *

urlpatterns = [
# ---------------------------------- CHATS ----------------------------------
    # path('chats/', ChatListAll.as_view()),
    path('chats/', ChatList.as_view()),
    # GET - List all chats
    # POST - Create a chat  | required field = chat_name(str)
    path('chats/<int:pk>/', ChatDetail.as_view()),
    # GET - Fetch a chat by ID
    # PUT - Update the chat    | only pass the updated fields
    # DELETE - Delete the chat

# ---------------------------------- MESSAGES ----------------------------------
    path('chats/<int:chat_id>/messages/', MessageList.as_view()),
    # GET - List all messages in a chat
    # POST - Create a message(question) inside that chat  | required field = message_text(str)
            # | This will take some time as it has to query metta files and prompt the llm 
            # | If successful, the response will be the user's question and the llm's answer (in markdown)
    path('messages/<int:pk>/', MessageDetail.as_view()),
    # GET - Fetch a message by ID
    # PUT - Update the message    | only pass the updated fields
    # DELETE - Delete the message

# ---------------------------------- EXAMPLES ----------------------------------
    path('examples/', ExampleList.as_view()),
    # GET - List all examples
    # POST - Create an example  | required fields = example_text(str)
    path('examples/<int:pk>/', ExampleDetail.as_view()),
    # GET - Fetch an example by ID
    # PUT - Update the example    | only pass the updated fields
    # DELETE - Delete the example

# ---------------------------------- SCHEMA ----------------------------------
    path('schema/', SchemaList.as_view()),
    # GET - List all entities in the schema
    # POST - Upload a new schema  | required fields= schema_file(file)
                                # | Send request as Multipart formdata

# ---------------------------------- ATOMSPACES ----------------------------------
    path('atomspaces/', AtomspaceList.as_view()),
    # GET - List all MeTTa files beloning to the schema
    # POST - Upload a MeTTa file for an entity  | required fields= entity_name(str), metta_file(file)
                                              # | Send request as Multipart formdata
    path('atomspaces/<int:pk>/', AtomspaceDetail.as_view()),
    # GET - Fetch atomspace data by ID
    # PUT - Update atomspace data    | only pass the updated fields
    # DELETE - Delete the atomspace data (along with the MeTTa files)
]