# -*- coding: utf-8 -*-
'''
    command line tool to convert NIfTI files to .msh to be read by gmsh
    This program is part of the SimNIBS package.
    Please check on www.simnibs.org how to cite our work in publications.

    Copyright (C) 2018  Guilherme B Saturnino, Kristoffer H Madsen, Axel Thieslcher,
    Jesper D Nielsen, Andre Antunes

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>

'''

import os
import sys
import argparse
import nibabel

import simnibs.mesh_tools.mesh_io as mesh_io
import simnibs.utils.cond_utils
from simnibs.utils.simnibs_logger import logger
from ..utils.mesh_element_properties import ElementTags
from simnibs import __version__


def parseArguments(argv):

    parser = argparse.ArgumentParser(prog="nifti2msh", description="Interpolate field in "
                                     "NifTI file to mesh. Uses information in the"
                                     " qform and sform to define the transformation from"
                                     " the nifti to the mesh")
    parser.add_argument("fn_nifti", help="Input nifti file")
    parser.add_argument("fn_mesh", help="Input mesh file")
    parser.add_argument('fn_out', help="Output file name")
    parser.add_argument("-ev", action="store_true",
                        help="If the NifTI contains a tensor, save only the maximum "
                        "eigenvector in brain tissue - e.g. for visual control")
    parser.add_argument('--type', default='elements', choices=['elements', 'nodes'],
                        help=
                        "Whether to store field in mesh elements or nodes. "
                        "Default: elements"
                       )
    parser.add_argument('--version', action='version', version=__version__)
    return parser.parse_args(argv)


def main():
    args = parseArguments(sys.argv[1:])
    if not os.path.isfile(args.fn_nifti):
        raise IOError('Could not find file: {0}'.format(args.fn_nifti))
    if not os.path.isfile(args.fn_mesh):
        raise IOError('Could not find file: {0}'.format(args.fn_mesh))
    image = nibabel.load(args.fn_nifti)
    mesh = mesh_io.read_msh(args.fn_mesh)
    vol = image.dataobj
    affine = image.affine
    if args.ev:
        logger.info('Creating tensor visualization')
        mesh = mesh.crop_mesh([ElementTags.WM, ElementTags.GM, ElementTags.WM_TH_SURFACE, ElementTags.GM_TH_SURFACE])
        cond_list = [c.value for c in simnibs.utils.cond_utils.standard_cond()]
        sigma = simnibs.utils.cond_utils.cond2elmdata(mesh, cond_list, anisotropy_volume=vol, affine=affine,
                                  aniso_tissues=[ElementTags.WM, ElementTags.GM])
        views = simnibs.utils.cond_utils.visualize_tensor(sigma, mesh)
        mesh.nodedata = []
        mesh.elmdata = views
        mesh_io.write_msh(mesh, args.fn_out)
    else:
        logger.info('Interpolating data in NifTI file to mesh')
        if args.type == 'elements':
            ed = mesh_io.ElementData.from_data_grid(
                    mesh, vol, affine, 'from_volume'
            )
            mesh.elmdata.append(ed)
        if args.type == 'nodes':
            nd = mesh_io.NodeData.from_data_grid(
                    mesh, vol, affine, 'from_volume'
            )
            mesh.nodedata.append(nd)
        mesh_io.write_msh(mesh, args.fn_out)


if __name__ == '__main__':
    main()
