from django.db import models

# Create your models here.
class sepa_log(models.Model):
    id = models.AutoField(primary_key=True)
    id_branch = models.ForeignKey(sepa_branch, to_field='id', on_delete=models.CASCADE)
    id_usuario = models.ForeignKey(user, to_field='id', on_delete=models.CASCADE,db_constraint=False)
    tipo_movimiento = models.CharField(max_length=120,blank=True)
    tabla = models.CharField(max_length=120,blank=True)
    id_row = models.IntegerField(blank=True,null=True)
    sql_query = models.TextField(blank=True,null=True)
    post = models.TextField(blank=True,null=True)
    url = models.CharField(max_length=2048,blank=True,null=True)
    fecha_creacion = models.DateTimeField(auto_now=False, auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=False, auto_now_add=True)
    idDevice = models.IntegerField(blank=True,null=True)
    idConnection = models.IntegerField(blank=True,null=True)
    eliminado = models.BooleanField(default=False)
    origen = models.CharField(max_length=2000,blank=True,null=True)
    def __str__(self):
        return self.id
    class Meta:
        db_table = "sepa_log"
    
class sepa_branch_details(models.Model):
    id = models.AutoField(primary_key=True)
    branch = models.ForeignKey(sepa_branch, on_delete=models.CASCADE)
    username = models.CharField(max_length=255,blank=True)
    password = models.CharField(max_length=255,blank=True)

    def __str__(self):
        return f"{{ \"id\": \"{self.id}\", \"branch_id\": \" {self.branch_id}\", \"username\": \"{self.username}\", \"password\": \"{self.password}\" }}"

    class Meta:
        db_table = "pilot_branch_connection"