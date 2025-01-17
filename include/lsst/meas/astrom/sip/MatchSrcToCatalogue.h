// -*- LSST-C++ -*-

/* 
 * LSST Data Management System
 * Copyright 2008, 2009, 2010 LSST Corporation.
 * 
 * This product includes software developed by the
 * LSST Project (http://www.lsst.org/).
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the LSST License Statement and 
 * the GNU General Public License along with this program.  If not, 
 * see <http://www.lsstcorp.org/LegalNotices/>.
 */
 

#ifndef MATCH_SRC_TO_CATALOGUE
#define MATCH_SRC_TO_CATALOGUE

#include <iostream>
#include <cmath>

#include "lsst/base.h"
#include "lsst/pex/exceptions/Runtime.h"
#include "lsst/afw/table/Match.h"
#include "lsst/afw/geom/Angle.h"

namespace lsst {
    namespace afw {
        namespace image {
            class Wcs;
        }
    }
namespace meas { 
namespace astrom { 
namespace sip {

/// Match a SourceSet of objects with known ra/dec with a SourceSet of objects with known xy positions
/// Take a catalogue of objects with known positions, a catalogue of objects with known xy, and a wcs
/// to convert one xy <--> ra/dec. This class then finds the set of objects with common ra/dec.
///
/// The simplest usage is to create an object of this class, then access the corresponence sets with
/// getMatchedImgSet() and getMatchedCatSet(). Creating the object automatically calculates the sets
/// of corresponences for you. If you are unhappy with these matches, you can change one or more of your
/// input arguments and redo the match with findMatches()
///
/// Using this class has the side effect of updating the coord field of the input SourceCatalog (which
/// may be desirable).
class MatchSrcToCatalogue{
public:

    typedef boost::shared_ptr<MatchSrcToCatalogue> Ptr;
    typedef boost::shared_ptr<MatchSrcToCatalogue const> ConstPtr;
    
    MatchSrcToCatalogue(afw::table::SimpleCatalog const& catSet,
                        afw::table::SourceCatalog const& imgSet,       
                        CONST_PTR(afw::image::Wcs) wcs,   
                        afw::geom::Angle dist
                       );

    //Mutators
    void setDist(afw::geom::Angle dist);
    void setWcs(CONST_PTR(afw::image::Wcs) wcs);
    void setCatSrcSet(afw::table::SimpleCatalog const & catSet);
    void setImgSrcSet(afw::table::SourceCatalog const & srcSet);

    void findMatches();

    //Accessors
    afw::table::ReferenceMatchVector getMatches();
    

private:
    afw::table::SimpleCatalog _catSet;       ///< Copy of input catalog
    afw::table::SourceCatalog _imgSet;       ///< Copy of input catalog
    afw::table::ReferenceMatchVector _match;    ///List of tuples of matching indices
    CONST_PTR(lsst::afw::image::Wcs) _wcs;
    lsst::afw::geom::Angle _dist;              ///< How close must two objects be to match 

    void _removeOneToMany();
    void _removeManyToOne();
};



}}}}

#endif

                

