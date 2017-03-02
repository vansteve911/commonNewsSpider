from .parsers.default import DefaultSiteParser
from .parsers.aawsat import AawsatSiteParser
from .parsers.almowaten import AlmowatenSiteParser
from .parsers.hasatoday import HasatodaySiteParser
from .parsers.alarabiya import AlarabiyaSiteParser
from .parsers.alhayat import AlhayatSiteParser
from .parsers.bab import BabSiteParser
from .parsers.nas import NasSiteParser
from .parsers.albawaba import AlbawabaSiteParser
from .parsers.alyaum import AlyaumSiteParser
from .parsers.aljazirahonline import AljazirahOnlineSiteParser
from .parsers.elaph import ElaphSiteParser

def parser_factory(seed):
  if seed.startswith('aawsat_'):
    return AawsatSiteParser()
  elif seed.startswith('almowaten_'):
    return AlmowatenSiteParser()
  elif seed.startswith('hasatoday_'):
    return HasatodaySiteParser()
  elif seed.startswith('alarabiya_'):
    return AlarabiyaSiteParser()
  elif seed.startswith('alhayat_'):
    return AlhayatSiteParser()
  elif seed.startswith('bab_'):
    return BabSiteParser()
  elif seed.startswith('nas_'):
    return NasSiteParser()
  elif seed.startswith('albawaba_'):
    return AlbawabaSiteParser()
  elif seed.startswith('alyaum_'):
    return AlyaumSiteParser()
  elif seed.startswith('al-jazirahonline_'):
    return AljazirahOnlineSiteParser()
  elif seed.startswith('elaph_'):
    return ElaphSiteParser()
  return DefaultSiteParser()