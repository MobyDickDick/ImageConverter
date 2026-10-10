from pathlib import Path

import pytest

from src.iCCModules.imageCompositeConverterConversionFinalization import _archiveSuccessfulConversionArtifacts as archive
from src.iCCModules.imageCompositeConverterSuccessfulConversionQuality import findImagePathByVariantImpl


@pytest.mark.parametrize('failure',['missing_svg','raster_svg','failed_svg','blank_svg','empty_svg','invalid_svg'])
def test_sources_with_unusable_outputs_remain_in_intake(tmp_path,failure):
    inputs=tmp_path/'input';inputs.mkdir()
    svgs=tmp_path/'svg';svgs.mkdir()
    (inputs/'symbol.jpg').write_bytes(b'original')
    content={'raster_svg':'<svg><image href="payload.png"/></svg>',
             'empty_svg':'<svg/>','invalid_svg':'<svg><path',
             'blank_svg':'<svg><rect width="100%" height="100%" fill="white"/></svg>',
             'failed_svg':'<svg><circle r="3"/></svg>'}
    if failure!='missing_svg':
        (svgs/('Failed_SYMBOL.svg' if failure=='failed_svg' else 'SYMBOL.svg')).write_text(content[failure],encoding='utf-8')
    archive(folder_path=str(inputs),svg_out_dir=str(svgs),reports_out_dir=str(tmp_path/'reports'),
            result_map={'symbol.jpg':{'variant':'SYMBOL','status':'semantic_ok'}})
    assert (inputs/'symbol.jpg').read_bytes()==b'original'
    assert not (inputs/'succesessfulConvertedImages'/'symbol.jpg').exists()


def test_rechecking_archive_does_not_nest_it_or_overwrite_different_sources(tmp_path):
    inputs=tmp_path/'input';inputs.mkdir()
    accepted=inputs/'succesessfulConvertedImages';accepted.mkdir()
    svgs=tmp_path/'svg';svgs.mkdir()
    (svgs/'SYMBOL.svg').write_text('<svg><circle r="3"/></svg>',encoding='utf-8')
    (accepted/'Symbol.JPEG').write_bytes(b'original')
    assert Path(findImagePathByVariantImpl(str(inputs),'symbol'))==accepted/'Symbol.JPEG'
    archive(folder_path=str(accepted),svg_out_dir=str(svgs),reports_out_dir=str(tmp_path/'reports'),
        result_map={'Symbol.JPEG':{'variant':'SYMBOL','status':'semantic_ok'}})
    assert (accepted/'Symbol.JPEG').read_bytes()==b'original'
    assert not (accepted/'succesessfulConvertedImages').exists()
    (inputs/'Symbol.JPEG').write_bytes(b'different')
    with pytest.raises(ValueError,match='Different source already archived'):
        archive(folder_path=str(inputs),svg_out_dir=str(svgs),reports_out_dir=str(tmp_path/'reports'),
            result_map={'Symbol.JPEG':{'variant':'SYMBOL','status':'semantic_ok'}})
    assert (accepted/'Symbol.JPEG').read_bytes()==b'original'
    assert (inputs/'Symbol.JPEG').read_bytes()==b'different'


def test_source_lookup_keeps_jpeg_preference_and_prioritizes_intake(tmp_path):
    accepted=tmp_path/'succesessfulConvertedImages';accepted.mkdir()
    for path in (tmp_path/'Symbol.bmp',tmp_path/'Symbol.JPG',accepted/'Symbol.jpg'):
        path.write_bytes(b'pixels')
    assert Path(findImagePathByVariantImpl(str(tmp_path),'symbol'))==tmp_path/'Symbol.JPG'
