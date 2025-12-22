CREATE TABLE [dbo].[sepa_log] (
    id INT IDENTITY(1,1) PRIMARY KEY,
    id_branch_id INT NOT NULL, -- Django añade '_id' automáticamente a los campos ForeignKey
    id_usuario_id INT NOT NULL, -- Sin constraint física por db_constraint=False
    tipo_movimiento NVARCHAR(120) NOT NULL DEFAULT '',
    tabla NVARCHAR(120) NOT NULL DEFAULT '',
    id_row INT NULL,
    sql_query NVARCHAR(MAX) NULL,
    post NVARCHAR(MAX) NULL,
    url NVARCHAR(2048) NULL,
    fecha_creacion DATETIME2 NOT NULL DEFAULT GETDATE(),
    fecha_actualizacion DATETIME2 NOT NULL DEFAULT GETDATE(),
    idDevice INT NULL,
    idConnection INT NULL,
    eliminado BIT NOT NULL DEFAULT 0,
    origen NVARCHAR(2000) NULL,
);
GO
CREATE TABLE [dbo].[pilot_branch_connection](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[username] [varchar](255) NULL,
	[password] [varchar](255) NULL,
	[branch_id] [int] NULL
) ON [PRIMARY]
GO
ALTER TABLE [dbo].[pilot_branch_connection] ADD PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
