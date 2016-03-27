#
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
import numpy

import lsst.pex.config as pexConfig
import lsst.afw.display.ds9 as ds9
import lsst.afw.math as afwMath
import lsst.meas.algorithms as measAlg


class CatalogStarSelectorConfig(pexConfig.Config):
    fluxLim = pexConfig.Field(
        doc = "specify the minimum psfFlux for good Psf Candidates",
        dtype = float,
        default = 0.0,
        check = lambda x: x >= 0.0,
    )
    fluxMax = pexConfig.Field(
        doc = "specify the maximum psfFlux for good Psf Candidates (ignored if == 0)",
        dtype = float,
        default = 0.0,
        #        minValue = 0.0,
        check = lambda x: x >= 0.0,
    )
    badStarPixelFlags = pexConfig.ListField(
        doc = "PSF candidate objects may not have any of these bits set",
        dtype = str,
        default = ["base_PixelFlags_flag_edge", "base_PixelFlags_flag_interpolatedCenter",
                   "base_PixelFlags_flag_saturatedCenter"],
    )
    kernelSize = pexConfig.Field(
        doc = "size of the kernel to create",
        dtype = int,
        default = 21,
    )
    borderWidth = pexConfig.Field(
        doc = "number of pixels to ignore around the edge of PSF candidate postage stamps",
        dtype = int,
        default = 0,
    )


class CheckSource(object):
    """A functor to check whether a source has any flags set that should cause it to be labeled bad."""

    def __init__(self, table, fluxLim, fluxMax, badStarPixelFlags):
        self.keys = [table.getSchema().find(name).key for name in badStarPixelFlags]
        self.keys.append(table.getCentroidFlagKey())
        self.fluxLim = fluxLim
        self.fluxMax = fluxMax

    def __call__(self, source):
        for k in self.keys:
            if source.get(k):
                return False
        if self.fluxLim is not None and source.getPsfFlux() < self.fluxLim:  # ignore faint objects
            return False
        if self.fluxMax != 0.0 and source.getPsfFlux() > self.fluxMax:  # ignore bright objects
            return False
        return True


class CatalogStarSelector(object):
    ConfigClass = CatalogStarSelectorConfig
    usesMatches = True  # selectStars uses (requires) its matches argument

    def __init__(self, config=None):
        """Construct a star selector that uses second moments

        This is a naive algorithm and should be used with caution.

        @param[in] config: An instance of CatalogStarSelectorConfig
        """
        if not config:
            config = CatalogStarSelector.ConfigClass()

        self._kernelSize = config.kernelSize
        self._borderWidth = config.borderWidth
        self._fluxLim = config.fluxLim
        self._fluxMax = config.fluxMax
        self._badStarPixelFlags = config.badStarPixelFlags

    def selectStars(self, exposure, sourceCat, matches=None):
        """!Return a list of PSF candidates that represent likely stars

        A list of PSF candidates may be used by a PSF fitter to construct a PSF.

        @param[in] exposure  the exposure containing the sources
        @param[in] sourceCat  catalog of sources that may be stars (an lsst.afw.table.SourceCatalog)
        @param[in] matches  a match vector as produced by meas_astrom; required
                            (defaults to None to match the StarSelector API and improve error handling)

        @return psfCandidateList: a list of PSF candidates.
        """
        import lsstDebug
        display = lsstDebug.Info(__name__).display
        displayExposure = lsstDebug.Info(__name__).displayExposure     # display the Exposure + spatialCells
        pauseAtEnd = lsstDebug.Info(__name__).pauseAtEnd               # pause when done

        if matches is None:
            raise RuntimeError("CatalogStarSelector requires matches")

        mi = exposure.getMaskedImage()

        if display:
            frames = {}
            if displayExposure:
                frames["displayExposure"] = 1
                ds9.mtv(mi, frame=frames["displayExposure"], title="PSF candidates")
        #
        # Read the reference catalogue
        #
        isGoodSource = CheckSource(sourceCat, self._fluxLim, self._fluxMax, self._badStarPixelFlags)

        #
        # Go through and find all the PSFs in the catalogue
        #
        # We'll split the image into a number of cells, each of which contributes only
        # one PSF candidate star
        #
        psfCandidateList = []

        with ds9.Buffering():
            for ref, source, d in matches:
                if not ref.get("resolved"):
                    if not isGoodSource(source):
                        symb, ctype = "+", ds9.RED
                    else:
                        try:
                            psfCandidate = measAlg.makePsfCandidate(source, exposure)

                            # The setXXX methods are class static, but it's convenient to call them on
                            # an instance as we don't know Exposure's pixel type
                            # (and hence psfCandidate's exact type)
                            if psfCandidate.getWidth() == 0:
                                psfCandidate.setBorderWidth(self._borderWidth)
                                psfCandidate.setWidth(self._kernelSize + 2*self._borderWidth)
                                psfCandidate.setHeight(self._kernelSize + 2*self._borderWidth)

                            im = psfCandidate.getMaskedImage().getImage()
                            max = afwMath.makeStatistics(im, afwMath.MAX).getValue()
                            if not numpy.isfinite(max):
                                continue
                            psfCandidateList.append(psfCandidate)

                            symb, ctype = "+", ds9.GREEN
                        except Exception as err:
                            symb, ctype = "o", ds9.RED
                            print "RHL", err
                            pass  # FIXME: should log this!
                else:
                    symb, ctype = "o", ds9.BLUE

                if display and displayExposure:
                    ds9.dot(symb, source.getX() - mi.getX0(), source.getY() - mi.getY0(),
                            size=4, frame=frames["displayExposure"], ctype=ctype)

        if display and pauseAtEnd:
            raw_input("Continue? y[es] p[db] ")

        return psfCandidateList

measAlg.starSelectorRegistry.register("catalog", CatalogStarSelector)
