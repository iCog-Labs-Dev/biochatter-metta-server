import os
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

class Chat(models.Model):
    # topic_id = models.ForeignKey(Topic, on_delete=models.CASCADE)
    chat_name = models.CharField(max_length=100)
    chat_created_at = models.DateTimeField(auto_now_add=True)
    chat_updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.chat_name

class Message(models.Model):
    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE)
    message_text = models.CharField(max_length=2000)
    is_user_message = models.BooleanField(default=True)
    message_created_at = models.DateTimeField(auto_now_add=True)
    message_updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return 'User Message' if self.is_user_message else 'LLM Message'

class Example(models.Model):
    example_text = models.CharField(max_length=900)
    
    def __str__(self) -> str:
        return self.example_title

class Setting(models.Model):
    message_context_length = models.IntegerField(default=10)
    openai_api_key = models.CharField(max_length=900)

class Schema(models.Model):
    def schema_file_path(instance, filename):
        base_filename, file_extension = os.path.splitext(filename)
        new_filename = f"schema_config{file_extension}"
        return os.path.join('api/bio_data/biocypher_schema', new_filename)

    schema_name = models.CharField(max_length=100, default='Schema', unique=True)
    schema_file = models.FileField(upload_to='api/bio_data/biocypher_schema')

class Atomspace(models.Model):
    def metta_file_path(instance, filename):
        base_filename, file_extension = os.path.splitext(filename)
        new_filename = f"{base_filename}{file_extension}"
        return os.path.join('api/bio_data/bioatomspace', new_filename)
        # new_filename = f"custom_prefix_{instance.pk}{file_extension}"
        # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
        # return "api/bio_data/bioatomspace/".format(instance.user.id, filename)

    db_name = models.CharField(max_length=100, unique=True)
    nodes = models.CharField(max_length=1000, default='[]')
    edges = models.CharField(max_length=1000, default='[]')
    node_metta_file = models.FileField(upload_to=metta_file_path, null=True)
    edge_metta_file = models.FileField(upload_to=metta_file_path, null=True)

# Delete the Schema when deleting the Schema record
@receiver(pre_delete, sender=Schema)
def delete_old_schema(sender, instance, **kwargs):
    # Delete the Schema file from the file system
    if instance.schema_file and os.path.isfile(instance.schema_file.path):
        os.remove(instance.schema_file.path)

# Delete the MeTTa file of a deleted Atomspace record
@receiver(pre_delete, sender=Atomspace)
def delete_metta_file(sender, instance, **kwargs):
    # Delete the MeTTa files from the file system
    if instance.node_metta_file and os.path.isfile(instance.node_metta_file.path):
        os.remove(instance.node_metta_file.path)

    if instance.edge_metta_file and os.path.isfile(instance.edge_metta_file.path):
        os.remove(instance.edge_metta_file.path)

# Delete old MeTTa file while updating (saving a new MeTTa file)
@receiver(pre_save, sender=Atomspace)
def delete_old_metta_file(sender, instance, **kwargs):
    # Check if the instance has been previously saved
    if instance.pk:
        # Retrieve the existing record from the database
        old_instance = sender.objects.get(pk=instance.pk)
        # Compare the old file path with the new file path
        if old_instance.node_metta_file != instance.node_metta_file:
            # Delete the old file if it exists
            if old_instance.node_metta_file and os.path.isfile(old_instance.node_metta_file.path):
                os.remove(old_instance.node_metta_file.path)
        
        if old_instance.edge_metta_file != instance.edge_metta_file:
            if old_instance.edge_metta_file and os.path.isfile(old_instance.edge_metta_file.path):
                os.remove(old_instance.edge_metta_file.path)



