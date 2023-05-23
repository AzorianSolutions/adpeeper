from pyad import adquery, pyad

base_dn: str = 'OU=Managed Users,OU=Managed Resources,DC=root,DC=local'
employee_attributes: list = ['employeeID', 'distinguishedName', 'samAccountName', 'displayName']
q = adquery.ADQuery()

employee = pyad.from_dn('CN=Jeff Grothouse,OU=Field Crew,OU=Bristol,OU=Users,OU=Managed Users,OU=Managed Resources,'
                        'DC=root,DC=local')

# print(employee.get_mandatory_attributes())

q.execute_query(
    attributes=employee_attributes,
    base_dn='OU=Managed Users,OU=Managed Resources,DC=root,DC=local',
    search_scope='subtree'
)

for row in q.get_results():
    # ad_object = pyad.from_dn(row['distinguishedName'])
    if row['samAccountName'] in ['matt.scott']:
        print(row)
        # ad_object = pyad.from_dn(row['distinguishedName'])
        # ad_object.update_attribute('employeeID', '0123456789')
    pass
