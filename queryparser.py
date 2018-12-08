import re
from django.db.models import Q

# check if string can be converted to a float
def is_float(input):
  try:
    num = float(input)
  except ValueError:
    return False
  return True

# check if string can be converted to an integer
def is_int(input):
  try:
    num = int(input)
  except ValueError:
    return False
  return True

# convert string value to a valid python type
def get_value(strValue):
    if strValue.startswith('"') and strValue.endswith('"'):
        return strValue.replace('"','')
    elif is_int(strValue):
        return int(strValue)
    elif is_float(strValue):
        return float(strValue)
    elif strValue.capitalize() == "True":
        return True
    elif strValue.capitalize() == "False":
        return False
    elif strValue.lower() == "null":
        return None
    else:
        return strValue

class QuerySetFilter:
    # mapping of defined operators to the correct field lookkup value (https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups)
    OPERATORS = {
        '!='    : '!exact',
        '=='    : 'exact',
        '~='    : 'iexact',
        '!@'    : '!contains',
        '@@'    : 'contains',
        '~@'    : 'icontains',
        '<='    : 'lte',
        '>='    : 'gte',
        '=%'    : 'startswith',
        '~%'    : 'istartswith',
        '%='    : 'endswith',
        '%~'    : 'iendswith',    
        '<'     : 'lt',
        '>'     : 'gt',
    }

    objName = None

    def __init__(self,objName=None):
        self.objName = objName

    # parses an input string of the form "<field>" or "<field> <operator> <value>" and 
    # returns a tuple (field, lookup_type, value) with the operator converted to correct field lookkup (https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups) and
    # value converted to correct python type

    def parse(self, input):
        field, lookup_type, value = None, None, None
        rex='(' + '|'.join(list(self.OPERATORS)) + ')'

        parts = re.split(rex,input)
        length = len(parts)

        # if when splitting we get two or more than three value, then there is a problem so return None values
        if length == 2 | length > 3 :
            return (field, lookup_type, value)

        field = parts[0].strip()

        if len(parts) == 3:
            lookup_type = self.OPERATORS.get(parts[1].strip())
            value = get_value(parts[-1].strip())

        return (field, lookup_type, value)


    # parses an input string of the form "<field>" or "<field> <operator> <value>" and 
    # returns a Q object (https://docs.djangoproject.com/en/dev/ref/models/querysets/#q-objects)
    # will check to see if the string begins with #Q, which means the string is alread converted to a Q object

    def get_Q(self, value):
        if value.startswith('#Q'):
            return None

        field, lookup_type, value = self.parse(value)
        lookup_type = lookup_type or 'exact'

        qNot = lookup_type.startswith('!')
        lookup_type = lookup_type.lstrip('!')

        if self.objName is not None:
            query_arg = '{}__{}__{}'.format(self.objName, field, lookup_type)
        else:
            query_arg = '{}__{}'.format(field, lookup_type)
        
        query = {query_arg:value}

        return ~Q(**query) if qNot else Q(**query)

    # parses a simple query separated by either & or | and returns a Q object
    # i.e. 'age > 50 & sex=m' returns: <Q: (AND: ('properties__age__gt', 50), ('properties__sex=m__exact', None))>

    def combine(self, qryStr, qs):
        rex = '[&|]'
        
        indx = 0
        queries = re.split(rex,qryStr)
        update = self.get_Q(queries[indx]) or qs.get(queries[indx].strip())

        for oper in re.findall(rex,qryStr):
            indx += 1
            if indx == len(queries):
                break

            query = self.get_Q(queries[indx]) or qs.get(queries[indx].strip())

            if oper == '&':
                update = update & query        
            else:
                update = update | query

        return update

    # parses a complex string query to a final Q Object
    # i.e. converts ( last=jones & first=joe) | age > 50  to
    #  <Q: (OR: (AND: last=jones, first=joe), (AND: age__gt, 50))>

    def get_Query(self, query):
        parRex = "\([^\(\)]+\)"
        qs = {}

        while True:
            indx=0
            qr = {}

            for match in re.finditer(parRex,query):
                qi='#Q{}'.format(indx)
                indx +=  1

                qryStr = match.group(0)         # get string within parens
                qryStr = qryStr.strip('() ')    # strip trailing & leading paren's and blanks

                qr[qi]=self.combine(qryStr,qs)
                query=query[:match.start()] + qi + query[match.end():]  # replace query string with query name lookup

            qs = qr

            if re.search(parRex,query) == None:
                return self.combine(query,qs)

