# DJangoQuerySetFilter
Allows natural language filtering of Django QuerySet

Example usage on a query set where properties is a PostGres Json Field.  

      query = QuerySetFilter('properties').get_Query('last ~= jones & city==New York') 
      return queryset.filter(query)
        
 
 This will filter for records where properties.last = 'jones' and properties.city = 'New York'. Note: ~= is a case-insensitive exact match.
 
