from __future__ import absolute_import, division, print_function

from lsst.daf.base import PropertyList
from lsst.afw.geom import Box2D
from lsst.afw.image.utils import getDistortedWcs

__all__ = ["createMatchMetadata"]


def createMatchMetadata(exposure):
    """Create metadata required for unpersisting a match list

    @param[in] exposure  exposure for which to create metadata

    @return metadata about the field (a daf_base PropertyList)
    """
    matchMeta = PropertyList()
    bboxd = Box2D(exposure.getBBox())
    ctrPos = bboxd.getCenter()
    wcs = getDistortedWcs(exposure.getInfo())
    ctrCoord = wcs.pixelToSky(ctrPos).toIcrs()
    llCoord = wcs.pixelToSky(bboxd.getMin())
    approxRadius = ctrCoord.angularSeparation(llCoord)
    matchMeta.add('RA', ctrCoord.getRa().asDegrees(), 'field center in degrees')
    matchMeta.add('DEC', ctrCoord.getDec().asDegrees(), 'field center in degrees')
    matchMeta.add('RADIUS', approxRadius.asDegrees(), 'field radius in degrees, approximate')
    matchMeta.add('SMATCHV', 1, 'SourceMatchVector version number')
    filterName = exposure.getFilter().getName() or None
    if filterName is not None and filterName not in ("_unknmown_", ""):
        matchMeta.add('FILTER', filterName, 'filter name for tagalong data')
    return matchMeta
