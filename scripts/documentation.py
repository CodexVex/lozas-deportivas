import os
from pathlib import Path
from sqlalchemy import create_engine,inspect
engine=create_engine(os.environ['DATABASE_URL']); inspector=inspect(engine)
Path('docs').mkdir(exist_ok=True)
lines=['# Diccionario de datos','', 'Generado automáticamente desde la base de datos.','']
er=['erDiagram']
for table in inspector.get_table_names():
    lines += [f'## {table}','','| Campo | Tipo | Nulo | Clave |','|---|---|---|---|']
    pk=inspector.get_pk_constraint(table)['constrained_columns']
    fk={c for f in inspector.get_foreign_keys(table) for c in f['constrained_columns']}
    er.append('  '+table+' {')
    for c in inspector.get_columns(table):
        key='PK' if c['name'] in pk else 'FK' if c['name'] in fk else ''
        lines.append(f"| {c['name']} | {c['type']} | {'Sí' if c['nullable'] else 'No'} | {key} |")
        typename=str(c['type']).split('(')[0].replace(' ','_')
        er.append(f"    {typename} {c['name']} {key}".rstrip())
    er.append('  }');lines.append('')
    for f in inspector.get_foreign_keys(table):
        er.append('  '+f['referred_table']+' ||--o{ '+table+' : "'+','.join(f['constrained_columns'])+'"')
Path('docs/diccionario.md').write_text('\n'.join(lines)+'\n')
Path('docs/er.mmd').write_text('\n'.join(er)+'\n')
Path('docs/diagrama.md').write_text('# Diagrama entidad relación\n\n```mermaid\n'+'\n'.join(er)+'\n```\n')
