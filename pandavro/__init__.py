import fastavro
import numpy as np
import pandas as pd


def __type_infer(t: np.dtype):
    if t == np.bool_:
        return 'boolean'
    elif t == (np.int8 or np.int16 or np.int32):
        return 'int'
    elif t == np.int64:
        return 'long'
    elif t == np.float32:
        return 'float'
    elif t == np.float64:
        return 'double'
    elif t == np.object:
        # TODO: Dealing with the case of collection.
        return 'string'
    else:
        raise TypeError('Invalid type: {}'.format(t))


def __fields_infer(df: pd.DataFrame):
    fields = []
    for key, type_np in df.dtypes.iteritems():
        type_avro = __type_infer(type_np)
        fields.append({'name': key, 'type': ['null', type_avro]})
    return fields


def __schema_infer(df):
    fields = __fields_infer(df)
    schema = {
        'type': 'record',
        'name': 'Root',
        'fields': fields
    }
    return schema


def __file_to_dataframe_direct(f, schema):
    reader = fastavro.reader(f, reader_schema=schema)
    return pd.DataFrame.from_records(list(reader))


def __file_to_dataframe_gen(f, chunksize, schema):
    reader = fastavro.reader(f, reader_schema=schema)
    record_list = []
    for i, record in enumerate(reader):
        record_list.append(record)
        if (i + 1) % chunksize == 0:
            yield pd.DataFrame.from_records(record_list)
            record_list = []
    yield pd.DataFrame.from_records(record_list)
            

def __from_avro_gen(file_buffer, schema, chunksize):
    df_gen = __file_to_dataframe_gen(file_buffer, schema, chunksize)
    for df in df_gen:
        yield df


def __from_avro_direct(file_buffer, schema):
    return __file_to_dataframe(file_path_or_buffer, schema)


def from_avro(file_path_or_buffer, schema=None, chunksize=None):
    """
    Avro file reader.

    Args:
        file_path_or_buffer: Input file path or file-like object.
        schema: Avro schema.
        chunksize: The number of 

    Returns:
        pd.DataFrame or a pd.DataFrame generator if chunksize specified
    """
    if isinstance(file_path_or_buffer, str):
        file_buffer = open(file_path_or_buffer, 'rb')
    else:
        file_buffer = file_path_or_buffer

    if chunksize is None:
        return __from_avro_direct(file_buffer, schema)
    else:
        return __from_avro_gen(file_buffer, schema, chunksize)


def to_avro(file_path, df, schema=None):
    """
    Avro file writer.

    Args:
        file_path: Output file path.
        df: pd.DataFrame.
        schema: Dict of Avro schema.
            If it's set None, inferring schema.
    """

    if schema is None:
        schema = __schema_infer(df)

    with open(file_path, 'wb') as f:
        fastavro.writer(f, schema=schema,
                        records=df.to_dict('records'))
