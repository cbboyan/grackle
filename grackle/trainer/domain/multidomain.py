from .customdomain import CustomDomain

class MultiDomain(CustomDomain):
   
   def __init__(self, domains):
      CustomDomain.__init__(self)
      for domain in domains:
         self.add_domain(domain)
   
   def __repr__(self):
      args = [repr(dom) for dom in self._domains]
      return f"{type(self).__name__}([{','.join(args)}])"

   def reset(self):
      super().reset()
      self._domains = []

   def add_domain(self, domain):
      self._params.update(domain.params)
      self._defaults.update(domain.defaults)
      self._conditions.extend(domain.conditions)
      self._forbiddens.extend(domain.forbiddens)
      self._domains.append(domain)
