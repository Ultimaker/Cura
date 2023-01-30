# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

_REMOVED_SETTINGS = {
    "limit_support_retractions",
    "material_flow_dependent_temperature",
}

_RENAMED_PROFILES = {
    "um_s3_aa0.25_ABS_Normal_Quality": "um_s3_aa0.25_abs_0.1mm",
    "um_s3_aa0.25_CPE_Normal_Quality": "um_s3_aa0.25_cpe_0.1mm",
    "um_s3_aa0.25_Nylon_Normal_Quality": "um_s3_aa0.25_nylon_0.1mm",
    "um_s3_aa0.25_PC_Normal_Quality": "um_s3_aa0.25_pc_0.1mm",
    "um_s3_aa0.25_PETG_Normal_Quality": "um_s3_aa0.25_petg_0.1mm",
    "um_s3_aa0.25_PLA_Normal_Quality": "um_s3_aa0.25_pla_0.1mm",
    "um_s3_aa0.25_PP_Normal_Quality": "um_s3_aa0.25_pp_0.1mm",
    "um_s3_aa0.25_TPLA_Normal_Quality": "um_s3_aa0.25_tough-pla_0.1mm",
    "um_s3_aa0.4_ABS_Draft_Print": "um_s3_aa0.4_abs_0.2mm",
    "um_s3_aa0.4_ABS_Draft_Print_Quick": "um_s3_aa0.4_abs_0.2mm_quick",
    "um_s3_aa0.4_ABS_Fast_Print": "um_s3_aa0.4_abs_0.15mm",
    "um_s3_aa0.4_ABS_Fast_Print_Accurate": "um_s3_aa0.4_abs_0.15mm_engineering",
    "um_s3_aa0.4_ABS_Fast_Visual": "um_s3_aa0.4_abs_0.15mm_visual",
    "um_s3_aa0.4_ABS_High_Quality": "um_s3_aa0.4_abs_0.06mm",
    "um_s3_aa0.4_ABS_High_Visual": "um_s3_aa0.4_abs_0.06mm_visual",
    "um_s3_aa0.4_ABS_Normal_Quality": "um_s3_aa0.4_abs_0.1mm",
    "um_s3_aa0.4_ABS_Normal_Quality_Accurate": "um_s3_aa0.4_abs_0.1mm_engineering",
    "um_s3_aa0.4_ABS_Normal_Visual": "um_s3_aa0.4_abs_0.1mm_visual",
    "um_s3_aa0.4_BAM_Draft_Print": "um_s3_aa0.4_bam_0.2mm",
    "um_s3_aa0.4_BAM_Fast_Print": "um_s3_aa0.4_bam_0.15mm",
    "um_s3_aa0.4_BAM_Normal_Quality": "um_s3_aa0.4_bam_0.1mm",
    "um_s3_aa0.4_BAM_VeryDraft_Print": "um_s3_aa0.4_bam_0.3mm",
    "um_s3_aa0.4_CPE_Draft_Print": "um_s3_aa0.4_cpe_0.2mm",
    "um_s3_aa0.4_CPE_Fast_Print": "um_s3_aa0.4_cpe_0.15mm",
    "um_s3_aa0.4_CPE_Fast_Print_Accurate": "um_s3_aa0.4_cpe_0.15mm_engineering",
    "um_s3_aa0.4_CPE_High_Quality": "um_s3_aa0.4_cpe_0.06mm",
    "um_s3_aa0.4_CPE_Normal_Quality": "um_s3_aa0.4_cpe_0.1mm",
    "um_s3_aa0.4_CPE_Normal_Quality_Accurate": "um_s3_aa0.4_cpe_0.1mm_engineering",
    "um_s3_aa0.4_CPEP_Draft_Print": "um_s3_aa0.4_cpe-plus_0.2mm",
    "um_s3_aa0.4_CPEP_Fast_Print": "um_s3_aa0.4_cpe-plus_0.15mm",
    "um_s3_aa0.4_CPEP_Fast_Print_Accurate": "um_s3_aa0.4_cpe-plus_0.15mm_engineering",
    "um_s3_aa0.4_CPEP_High_Quality": "um_s3_aa0.4_cpe-plus_0.06mm",
    "um_s3_aa0.4_CPEP_Normal_Quality": "um_s3_aa0.4_cpe-plus_0.1mm",
    "um_s3_aa0.4_CPEP_Normal_Quality_Accurate": "um_s3_aa0.4_cpe-plus_0.1mm_engineering",
    "um_s3_aa0.4_Nylon_Draft_Print": "um_s3_aa0.4_nylon_0.2mm",
    "um_s3_aa0.4_Nylon_Fast_Print": "um_s3_aa0.4_nylon_0.15mm",
    "um_s3_aa0.4_Nylon_Fast_Print_Accurate": "um_s3_aa0.4_nylon_0.15mm_engineering",
    "um_s3_aa0.4_Nylon_High_Quality": "um_s3_aa0.4_nylon_0.06mm",
    "um_s3_aa0.4_Nylon_Normal_Quality": "um_s3_aa0.4_nylon_0.1mm",
    "um_s3_aa0.4_Nylon_Normal_Quality_Accurate": "um_s3_aa0.4_nylon_0.1mm_engineering",
    "um_s3_aa0.4_PC_Draft_Print": "um_s3_aa0.4_pc_0.2mm",
    "um_s3_aa0.4_PC_Fast_Print": "um_s3_aa0.4_pc_0.15mm",
    "um_s3_aa0.4_PC_Fast_Print_Accurate": "um_s3_aa0.4_pc_0.15mm_engineering",
    "um_s3_aa0.4_PC_High_Quality": "um_s3_aa0.4_pc_0.06mm",
    "um_s3_aa0.4_PC_Normal_Quality": "um_s3_aa0.4_pc_0.1mm",
    "um_s3_aa0.4_PC_Normal_Quality_Accurate": "um_s3_aa0.4_pc_0.1mm_engineering",
    "um_s3_aa0.4_PETG_Draft_Print": "um_s3_aa0.4_petg_0.2mm",
    "um_s3_aa0.4_PETG_Fast_Print": "um_s3_aa0.4_petg_0.15mm",
    "um_s3_aa0.4_PETG_Fast_Print_Accurate": "um_s3_aa0.4_petg_0.15mm_engineering",
    "um_s3_aa0.4_PETG_High_Quality": "um_s3_aa0.4_petg_0.06mm",
    "um_s3_aa0.4_PETG_Normal_Quality": "um_s3_aa0.4_petg_0.1mm",
    "um_s3_aa0.4_PETG_Normal_Quality_Accurate": "um_s3_aa0.4_petg_0.1mm_engineering",
    "um_s3_aa0.4_PLA_Draft_Print": "um_s3_aa0.4_pla_0.2mm",
    "um_s3_aa0.4_PLA_Draft_Print_Quick": "um_s3_aa0.4_pla_0.2mm_quick",
    "um_s3_aa0.4_PLA_Fast_Print": "um_s3_aa0.4_pla_0.15mm",
    "um_s3_aa0.4_PLA_Fast_Print_Accurate": "um_s3_aa0.4_pla_0.15mm_engineering",
    "um_s3_aa0.4_PLA_Fast_Visual": "um_s3_aa0.4_pla_0.15mm_visual",
    "um_s3_aa0.4_PLA_High_Quality": "um_s3_aa0.4_pla_0.06mm",
    "um_s3_aa0.4_PLA_High_Visual": "um_s3_aa0.4_pla_0.06mm_visual",
    "um_s3_aa0.4_PLA_Normal_Quality": "um_s3_aa0.4_pla_0.1mm",
    "um_s3_aa0.4_PLA_Normal_Quality_Accurate": "um_s3_aa0.4_pla_0.1mm_engineering",
    "um_s3_aa0.4_PLA_Normal_Visual": "um_s3_aa0.4_pla_0.1mm_visual",
    "um_s3_aa0.4_PLA_VeryDraft_Print": "um_s3_aa0.4_pla_0.3mm",
    "um_s3_aa0.4_PLA_VeryDraft_Print_Quick": "um_s3_aa0.4_pla_0.3mm_quick",
    "um_s3_aa0.4_PP_Draft_Print": "um_s3_aa0.4_pp_0.2mm",
    "um_s3_aa0.4_PP_Fast_Print": "um_s3_aa0.4_pp_0.15mm",
    "um_s3_aa0.4_PP_Normal_Quality": "um_s3_aa0.4_pp_0.1mm",
    "um_s3_aa0.4_TPLA_Draft_Print": "um_s3_aa0.4_tough-pla_0.2mm",
    "um_s3_aa0.4_TPLA_Draft_Print_Quick": "um_s3_aa0.4_tough-pla_0.2mm_quick",
    "um_s3_aa0.4_TPLA_Fast_Print": "um_s3_aa0.4_tough-pla_0.15mm",
    "um_s3_aa0.4_TPLA_Fast_Print_Accurate": "um_s3_aa0.4_tough-pla_0.15mm_engineering",
    "um_s3_aa0.4_TPLA_Fast_Visual": "um_s3_aa0.4_tough-pla_0.15mm_visual",
    "um_s3_aa0.4_TPLA_High_Quality": "um_s3_aa0.4_tough-pla_0.06mm",
    "um_s3_aa0.4_TPLA_High_Visual": "um_s3_aa0.4_tough-pla_0.06mm_visual",
    "um_s3_aa0.4_TPLA_Normal_Quality": "um_s3_aa0.4_tough-pla_0.1mm",
    "um_s3_aa0.4_TPLA_Normal_Quality_Accurate": "um_s3_aa0.4_tough-pla_0.1mm_engineering",
    "um_s3_aa0.4_TPLA_Normal_Visual": "um_s3_aa0.4_tough-pla_0.1mm_visual",
    "um_s3_aa0.4_TPLA_VeryDraft_Print": "um_s3_aa0.4_tough-pla_0.3mm",
    "um_s3_aa0.4_TPLA_VeryDraft_Print_Quick": "um_s3_aa0.4_tough-pla_0.3mm_quick",
    "um_s3_aa0.4_TPU_Draft_Print": "um_s3_aa0.4_tpu_0.2mm",
    "um_s3_aa0.4_TPU_Fast_Print": "um_s3_aa0.4_tpu_0.15mm",
    "um_s3_aa0.4_TPU_Normal_Quality": "um_s3_aa0.4_tpu_0.1mm",
    "um_s3_aa0.8_ABS_Draft_Print": "um_s3_aa0.8_abs_0.2mm",
    "um_s3_aa0.8_ABS_Superdraft_Print": "um_s3_aa0.8_abs_0.4mm",
    "um_s3_aa0.8_ABS_VeryDraft_Print": "um_s3_aa0.8_abs_0.3mm",
    "um_s3_aa0.8_CPE_Draft_Print": "um_s3_aa0.8_cpe_0.2mm",
    "um_s3_aa0.8_CPE_Superdraft_Print": "um_s3_aa0.8_cpe_0.4mm",
    "um_s3_aa0.8_CPE_VeryDraft_Print": "um_s3_aa0.8_cpe_0.3mm",
    "um_s3_aa0.8_CPEP_Fast_Print": "um_s3_aa0.8_cpe-plus_0.2mm",
    "um_s3_aa0.8_CPEP_Superdraft_Print": "um_s3_aa0.8_cpe-plus_0.4mm",
    "um_s3_aa0.8_CPEP_VeryDraft_Print": "um_s3_aa0.8_cpe-plus_0.3mm",
    "um_s3_aa0.8_Nylon_Draft_Print": "um_s3_aa0.8_nylon_0.2mm",
    "um_s3_aa0.8_Nylon_Superdraft_Print": "um_s3_aa0.8_nylon_0.4mm",
    "um_s3_aa0.8_Nylon_VeryDraft_Print": "um_s3_aa0.8_nylon_0.3mm",
    "um_s3_aa0.8_PC_Fast_Print": "um_s3_aa0.8_pc_0.2mm",
    "um_s3_aa0.8_PC_Superdraft_Print": "um_s3_aa0.8_pc_0.4mm",
    "um_s3_aa0.8_PC_VeryDraft_Print": "um_s3_aa0.8_pc_0.3mm",
    "um_s3_aa0.8_PETG_Draft_Print": "um_s3_aa0.8_petg_0.2mm",
    "um_s3_aa0.8_PETG_Superdraft_Print": "um_s3_aa0.8_petg_0.4mm",
    "um_s3_aa0.8_PETG_VeryDraft_Print": "um_s3_aa0.8_petg_0.3mm",
    "um_s3_aa0.8_PLA_Draft_Print": "um_s3_aa0.8_pla_0.2mm",
    "um_s3_aa0.8_PLA_Superdraft_Print": "um_s3_aa0.8_pla_0.4mm",
    "um_s3_aa0.8_PLA_VeryDraft_Print": "um_s3_aa0.8_pla_0.3mm",
    "um_s3_aa0.8_PP_Draft_Print": "um_s3_aa0.8_pp_0.2mm",
    "um_s3_aa0.8_PP_Superdraft_Print": "um_s3_aa0.8_pp_0.4mm",
    "um_s3_aa0.8_PP_VeryDraft_Print": "um_s3_aa0.8_pp_0.3mm",
    "um_s3_aa0.8_TPLA_Draft_Print": "um_s3_aa0.8_tough-pla_0.2mm",
    "um_s3_aa0.8_TPLA_Superdraft_Print": "um_s3_aa0.8_tough-pla_0.4mm",
    "um_s3_aa0.8_TPLA_VeryDraft_Print": "um_s3_aa0.8_tough-pla_0.3mm",
    "um_s3_aa0.8_TPU_Draft_Print": "um_s3_aa0.8_tpu_0.2mm",
    "um_s3_aa0.8_TPU_Superdraft_Print": "um_s3_aa0.8_tpu_0.4mm",
    "um_s3_aa0.8_TPU_VeryDraft_Print": "um_s3_aa0.8_tpu_0.3mm",
    "um_s3_bb0.4_PVA_Draft_Print": "um_s3_bb0.4_pva_0.2mm",
    "um_s3_bb0.4_PVA_Fast_Print": "um_s3_bb0.4_pva_0.15mm",
    "um_s3_bb0.4_PVA_High_Quality": "um_s3_bb0.4_pva_0.06mm",
    "um_s3_bb0.4_PVA_Normal_Quality": "um_s3_bb0.4_pva_0.1mm",
    "um_s3_bb0.4_PVA_VeryDraft_Print": "um_s3_bb0.4_pva_0.3mm",
    "um_s3_bb0.8_PVA_Draft_Print": "um_s3_bb0.8_pva_0.2mm",
    "um_s3_bb0.8_PVA_Superdraft_Print": "um_s3_bb0.8_pva_0.4mm",
    "um_s3_bb0.8_PVA_VeryDraft_Print": "um_s3_bb0.8_pva_0.3mm",
    "um_s3_cc0.4_CFFCPE_Draft_Print": "um_s3_cc0.4_cffcpe_0.2mm",
    "um_s3_cc0.4_CFFCPE_Fast_Print": "um_s3_cc0.4_cffcpe_0.15mm",
    "um_s3_cc0.4_CFFPA_Draft_Print": "um_s3_cc0.4_cffpa_0.2mm",
    "um_s3_cc0.4_CFFPA_Fast_Print": "um_s3_cc0.4_cffpa_0.15mm",
    "um_s3_cc0.4_GFFCPE_Draft_Print": "um_s3_cc0.4_gffcpe_0.2mm",
    "um_s3_cc0.4_GFFCPE_Fast_Print": "um_s3_cc0.4_gffcpe_0.15mm",
    "um_s3_cc0.4_GFFPA_Draft_Print": "um_s3_cc0.4_gffpa_0.2mm",
    "um_s3_cc0.4_GFFPA_Fast_Print": "um_s3_cc0.4_gffpa_0.15mm",
    "um_s3_cc0.4_PLA_Draft_Print": "um_s3_cc0.4_pla_0.2mm",
    "um_s3_cc0.4_PLA_Fast_Print": "um_s3_cc0.4_pla_0.15mm",
    "um_s3_cc0.6_CFFCPE_Draft_Print": "um_s3_cc0.6_cffcpe_0.2mm",
    "um_s3_cc0.6_CFFPA_Draft_Print": "um_s3_cc0.6_cffpa_0.2mm",
    "um_s3_cc0.6_GFFCPE_Draft_Print": "um_s3_cc0.6_gffcpe_0.2mm",
    "um_s3_cc0.6_GFFPA_Draft_Print": "um_s3_cc0.6_gffpa_0.2mm",
    "um_s3_cc0.6_PLA_Draft_Print": "um_s3_cc0.6_pla_0.2mm",
    "um_s3_cc0.6_PLA_Fast_Print": "um_s3_cc0.6_pla_0.15mm",
    "um_s5_aa0.25_ABS_Normal_Quality": "um_s5_aa0.25_abs_0.1mm",
    "um_s5_aa0.25_CPE_Normal_Quality": "um_s5_aa0.25_cpe_0.1mm",
    "um_s5_aa0.25_Nylon_Normal_Quality": "um_s5_aa0.25_nylon_0.1mm",
    "um_s5_aa0.25_PC_Normal_Quality": "um_s5_aa0.25_pc_0.1mm",
    "um_s5_aa0.25_PETG_Normal_Quality": "um_s5_aa0.25_petg_0.1mm",
    "um_s5_aa0.25_PLA_Normal_Quality": "um_s5_aa0.25_pla_0.1mm",
    "um_s5_aa0.25_PP_Normal_Quality": "um_s5_aa0.25_pp_0.1mm",
    "um_s5_aa0.25_TPLA_Normal_Quality": "um_s5_aa0.25_tough-pla_0.1mm",
    "um_s5_aa0.4_ABS_Draft_Print": "um_s5_aa0.4_abs_0.2mm",
    "um_s5_aa0.4_ABS_Draft_Print_Quick": "um_s5_aa0.4_abs_0.2mm_quick",
    "um_s5_aa0.4_ABS_Fast_Print": "um_s5_aa0.4_abs_0.15mm",
    "um_s5_aa0.4_ABS_Fast_Print_Accurate": "um_s5_aa0.4_abs_0.15mm_engineering",
    "um_s5_aa0.4_ABS_Fast_Visual": "um_s5_aa0.4_abs_0.15mm_visual",
    "um_s5_aa0.4_ABS_High_Quality": "um_s5_aa0.4_abs_0.06mm",
    "um_s5_aa0.4_ABS_High_Visual": "um_s5_aa0.4_abs_0.06mm_visual",
    "um_s5_aa0.4_ABS_Normal_Quality": "um_s5_aa0.4_abs_0.1mm",
    "um_s5_aa0.4_ABS_Normal_Quality_Accurate": "um_s5_aa0.4_abs_0.1mm_engineering",
    "um_s5_aa0.4_ABS_Normal_Visual": "um_s5_aa0.4_abs_0.1mm_visual",
    "um_s5_aa0.4_BAM_Draft_Print": "um_s5_aa0.4_bam_0.2mm",
    "um_s5_aa0.4_BAM_Fast_Print": "um_s5_aa0.4_bam_0.15mm",
    "um_s5_aa0.4_BAM_Normal_Quality": "um_s5_aa0.4_bam_0.1mm",
    "um_s5_aa0.4_BAM_VeryDraft_Print": "um_s5_aa0.4_bam_0.3mm",
    "um_s5_aa0.4_CPE_Draft_Print": "um_s5_aa0.4_cpe_0.2mm",
    "um_s5_aa0.4_CPE_Fast_Print": "um_s5_aa0.4_cpe_0.15mm",
    "um_s5_aa0.4_CPE_Fast_Print_Accurate": "um_s5_aa0.4_cpe_0.15mm_engineering",
    "um_s5_aa0.4_CPE_High_Quality": "um_s5_aa0.4_cpe_0.06mm",
    "um_s5_aa0.4_CPE_Normal_Quality": "um_s5_aa0.4_cpe_0.1mm",
    "um_s5_aa0.4_CPE_Normal_Quality_Accurate": "um_s5_aa0.4_cpe_0.1mm_engineering",
    "um_s5_aa0.4_CPEP_Draft_Print": "um_s5_aa0.4_cpe-plus_0.2mm",
    "um_s5_aa0.4_CPEP_Fast_Print": "um_s5_aa0.4_cpe-plus_0.15mm",
    "um_s5_aa0.4_CPEP_Fast_Print_Accurate": "um_s5_aa0.4_cpe-plus_0.15mm_engineering",
    "um_s5_aa0.4_CPEP_High_Quality": "um_s5_aa0.4_cpe-plus_0.06mm",
    "um_s5_aa0.4_CPEP_Normal_Quality": "um_s5_aa0.4_cpe-plus_0.1mm",
    "um_s5_aa0.4_CPEP_Normal_Quality_Accurate": "um_s5_aa0.4_cpe-plus_0.1mm_engineering",
    "um_s5_aa0.4_Nylon_Draft_Print": "um_s5_aa0.4_nylon_0.2mm",
    "um_s5_aa0.4_Nylon_Fast_Print": "um_s5_aa0.4_nylon_0.15mm",
    "um_s5_aa0.4_Nylon_Fast_Print_Accurate": "um_s5_aa0.4_nylon_0.15mm_engineering",
    "um_s5_aa0.4_Nylon_High_Quality": "um_s5_aa0.4_nylon_0.06mm",
    "um_s5_aa0.4_Nylon_Normal_Quality": "um_s5_aa0.4_nylon_0.1mm",
    "um_s5_aa0.4_Nylon_Normal_Quality_Accurate": "um_s5_aa0.4_nylon_0.1mm_engineering",
    "um_s5_aa0.4_PC_Draft_Print": "um_s5_aa0.4_pc_0.2mm",
    "um_s5_aa0.4_PC_Fast_Print": "um_s5_aa0.4_pc_0.15mm",
    "um_s5_aa0.4_PC_Fast_Print_Accurate": "um_s5_aa0.4_pc_0.15mm_engineering",
    "um_s5_aa0.4_PC_High_Quality": "um_s5_aa0.4_pc_0.06mm",
    "um_s5_aa0.4_PC_Normal_Quality": "um_s5_aa0.4_pc_0.1mm",
    "um_s5_aa0.4_PC_Normal_Quality_Accurate": "um_s5_aa0.4_pc_0.1mm_engineering",
    "um_s5_aa0.4_PETG_Draft_Print": "um_s5_aa0.4_petg_0.2mm",
    "um_s5_aa0.4_PETG_Fast_Print": "um_s5_aa0.4_petg_0.15mm",
    "um_s5_aa0.4_PETG_Fast_Print_Accurate": "um_s5_aa0.4_petg_0.15mm_engineering",
    "um_s5_aa0.4_PETG_High_Quality": "um_s5_aa0.4_petg_0.06mm",
    "um_s5_aa0.4_PETG_Normal_Quality": "um_s5_aa0.4_petg_0.1mm",
    "um_s5_aa0.4_PETG_Normal_Quality_Accurate": "um_s5_aa0.4_petg_0.1mm_engineering",
    "um_s5_aa0.4_PLA_Draft_Print": "um_s5_aa0.4_pla_0.2mm",
    "um_s5_aa0.4_PLA_Draft_Print_Quick": "um_s5_aa0.4_pla_0.2mm_quick",
    "um_s5_aa0.4_PLA_Fast_Print": "um_s5_aa0.4_pla_0.15mm",
    "um_s5_aa0.4_PLA_Fast_Print_Accurate": "um_s5_aa0.4_pla_0.15mm_engineering",
    "um_s5_aa0.4_PLA_Fast_Visual": "um_s5_aa0.4_pla_0.15mm_visual",
    "um_s5_aa0.4_PLA_High_Quality": "um_s5_aa0.4_pla_0.06mm",
    "um_s5_aa0.4_PLA_High_Visual": "um_s5_aa0.4_pla_0.06mm_visual",
    "um_s5_aa0.4_PLA_Normal_Quality": "um_s5_aa0.4_pla_0.1mm",
    "um_s5_aa0.4_PLA_Normal_Quality_Accurate": "um_s5_aa0.4_pla_0.1mm_engineering",
    "um_s5_aa0.4_PLA_Normal_Visual": "um_s5_aa0.4_pla_0.1mm_visual",
    "um_s5_aa0.4_PLA_VeryDraft_Print": "um_s5_aa0.4_pla_0.3mm",
    "um_s5_aa0.4_PLA_VeryDraft_Print_Quick": "um_s5_aa0.4_pla_0.3mm_quick",
    "um_s5_aa0.4_PP_Draft_Print": "um_s5_aa0.4_pp_0.2mm",
    "um_s5_aa0.4_PP_Fast_Print": "um_s5_aa0.4_pp_0.15mm",
    "um_s5_aa0.4_PP_Normal_Quality": "um_s5_aa0.4_pp_0.1mm",
    "um_s5_aa0.4_TPLA_Draft_Print": "um_s5_aa0.4_tough-pla_0.2mm",
    "um_s5_aa0.4_TPLA_Draft_Print_Quick": "um_s5_aa0.4_tough-pla_0.2mm_quick",
    "um_s5_aa0.4_TPLA_Fast_Print": "um_s5_aa0.4_tough-pla_0.15mm",
    "um_s5_aa0.4_TPLA_Fast_Print_Accurate": "um_s5_aa0.4_tough-pla_0.15mm_engineering",
    "um_s5_aa0.4_TPLA_Fast_Visual": "um_s5_aa0.4_tough-pla_0.15mm_visual",
    "um_s5_aa0.4_TPLA_High_Quality": "um_s5_aa0.4_tough-pla_0.06mm",
    "um_s5_aa0.4_TPLA_High_Visual": "um_s5_aa0.4_tough-pla_0.06mm_visual",
    "um_s5_aa0.4_TPLA_Normal_Quality": "um_s5_aa0.4_tough-pla_0.1mm",
    "um_s5_aa0.4_TPLA_Normal_Quality_Accurate": "um_s5_aa0.4_tough-pla_0.1mm_engineering",
    "um_s5_aa0.4_TPLA_Normal_Visual": "um_s5_aa0.4_tough-pla_0.1mm_visual",
    "um_s5_aa0.4_TPLA_VeryDraft_Print": "um_s5_aa0.4_tough-pla_0.3mm",
    "um_s5_aa0.4_TPLA_VeryDraft_Print_Quick": "um_s5_aa0.4_tough-pla_0.3mm_quick",
    "um_s5_aa0.4_TPU_Draft_Print": "um_s5_aa0.4_tpu_0.2mm",
    "um_s5_aa0.4_TPU_Fast_Print": "um_s5_aa0.4_tpu_0.15mm",
    "um_s5_aa0.4_TPU_Normal_Quality": "um_s5_aa0.4_tpu_0.1mm",
    "um_s5_aa0.8_ABS_Draft_Print": "um_s5_aa0.8_abs_0.2mm",
    "um_s5_aa0.8_ABS_Superdraft_Print": "um_s5_aa0.8_abs_0.4mm",
    "um_s5_aa0.8_ABS_VeryDraft_Print": "um_s5_aa0.8_abs_0.3mm",
    "um_s5_aa0.8_CPE_Draft_Print": "um_s5_aa0.8_cpe_0.2mm",
    "um_s5_aa0.8_CPE_Superdraft_Print": "um_s5_aa0.8_cpe_0.4mm",
    "um_s5_aa0.8_CPE_VeryDraft_Print": "um_s5_aa0.8_cpe_0.3mm",
    "um_s5_aa0.8_CPEP_Fast_Print": "um_s5_aa0.8_cpe-plus_0.2mm",
    "um_s5_aa0.8_CPEP_Superdraft_Print": "um_s5_aa0.8_cpe-plus_0.4mm",
    "um_s5_aa0.8_CPEP_VeryDraft_Print": "um_s5_aa0.8_cpe-plus_0.3mm",
    "um_s5_aa0.8_Nylon_Draft_Print": "um_s5_aa0.8_nylon_0.2mm",
    "um_s5_aa0.8_Nylon_Superdraft_Print": "um_s5_aa0.8_nylon_0.4mm",
    "um_s5_aa0.8_Nylon_VeryDraft_Print": "um_s5_aa0.8_nylon_0.3mm",
    "um_s5_aa0.8_PC_Fast_Print": "um_s5_aa0.8_pc_0.2mm",
    "um_s5_aa0.8_PC_Superdraft_Print": "um_s5_aa0.8_pc_0.4mm",
    "um_s5_aa0.8_PC_VeryDraft_Print": "um_s5_aa0.8_pc_0.3mm",
    "um_s5_aa0.8_PETG_Draft_Print": "um_s5_aa0.8_petg_0.2mm",
    "um_s5_aa0.8_PETG_Superdraft_Print": "um_s5_aa0.8_petg_0.4mm",
    "um_s5_aa0.8_PETG_VeryDraft_Print": "um_s5_aa0.8_petg_0.3mm",
    "um_s5_aa0.8_PLA_Draft_Print": "um_s5_aa0.8_pla_0.2mm",
    "um_s5_aa0.8_PLA_Superdraft_Print": "um_s5_aa0.8_pla_0.4mm",
    "um_s5_aa0.8_PLA_VeryDraft_Print": "um_s5_aa0.8_pla_0.3mm",
    "um_s5_aa0.8_PP_Draft_Print": "um_s5_aa0.8_pp_0.2mm",
    "um_s5_aa0.8_PP_Superdraft_Print": "um_s5_aa0.8_pp_0.4mm",
    "um_s5_aa0.8_PP_VeryDraft_Print": "um_s5_aa0.8_pp_0.3mm",
    "um_s5_aa0.8_TPLA_Draft_Print": "um_s5_aa0.8_tough-pla_0.2mm",
    "um_s5_aa0.8_TPLA_Superdraft_Print": "um_s5_aa0.8_tough-pla_0.4mm",
    "um_s5_aa0.8_TPLA_VeryDraft_Print": "um_s5_aa0.8_tough-pla_0.3mm",
    "um_s5_aa0.8_TPU_Draft_Print": "um_s5_aa0.8_tpu_0.2mm",
    "um_s5_aa0.8_TPU_Superdraft_Print": "um_s5_aa0.8_tpu_0.4mm",
    "um_s5_aa0.8_TPU_VeryDraft_Print": "um_s5_aa0.8_tpu_0.3mm",
    "um_s5_bb0.4_PVA_Draft_Print": "um_s5_bb0.4_pva_0.2mm",
    "um_s5_bb0.4_PVA_Fast_Print": "um_s5_bb0.4_pva_0.15mm",
    "um_s5_bb0.4_PVA_High_Quality": "um_s5_bb0.4_pva_0.06mm",
    "um_s5_bb0.4_PVA_Normal_Quality": "um_s5_bb0.4_pva_0.1mm",
    "um_s5_bb0.4_PVA_VeryDraft_Print": "um_s5_bb0.4_pva_0.3mm",
    "um_s5_bb0.8_PVA_Draft_Print": "um_s5_bb0.8_pva_0.2mm",
    "um_s5_bb0.8_PVA_Superdraft_Print": "um_s5_bb0.8_pva_0.4mm",
    "um_s5_bb0.8_PVA_VeryDraft_Print": "um_s5_bb0.8_pva_0.3mm",
    "um_s5_cc0.4_CFFCPE_Draft_Print": "um_s5_cc0.4_cffcpe_0.2mm",
    "um_s5_cc0.4_CFFCPE_Fast_Print": "um_s5_cc0.4_cffcpe_0.15mm",
    "um_s5_cc0.4_CFFPA_Draft_Print": "um_s5_cc0.4_cffpa_0.2mm",
    "um_s5_cc0.4_CFFPA_Fast_Print": "um_s5_cc0.4_cffpa_0.15mm",
    "um_s5_cc0.4_GFFCPE_Draft_Print": "um_s5_cc0.4_gffcpe_0.2mm",
    "um_s5_cc0.4_GFFCPE_Fast_Print": "um_s5_cc0.4_gffcpe_0.15mm",
    "um_s5_cc0.4_GFFPA_Draft_Print": "um_s5_cc0.4_gffpa_0.2mm",
    "um_s5_cc0.4_GFFPA_Fast_Print": "um_s5_cc0.4_gffpa_0.15mm",
    "um_s5_cc0.4_PLA_Draft_Print": "um_s5_cc0.4_pla_0.2mm",
    "um_s5_cc0.4_PLA_Fast_Print": "um_s5_cc0.4_pla_0.15mm",
    "um_s5_cc0.6_CFFCPE_Draft_Print": "um_s5_cc0.6_cffcpe_0.2mm",
    "um_s5_cc0.6_CFFPA_Draft_Print": "um_s5_cc0.6_cffpa_0.2mm",
    "um_s5_cc0.6_GFFCPE_Draft_Print": "um_s5_cc0.6_gffcpe_0.2mm",
    "um_s5_cc0.6_GFFPA_Draft_Print": "um_s5_cc0.6_gffpa_0.2mm",
    "um_s5_cc0.6_PLA_Draft_Print": "um_s5_cc0.6_pla_0.2mm",
    "um_s5_cc0.6_PLA_Fast_Print": "um_s5_cc0.6_pla_0.15mm"
}

class VersionUpgrade52to53(VersionUpgrade):
    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades preferences to remove from the visibility list the settings that were removed in this version.
        It also changes the preferences to have the new version number.

        This removes any settings that were removed in the new Cura version.
        :param serialized: The original contents of the preferences file.
        :param filename: The file name of the preferences file.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "21"

        # Remove deleted settings from the visible settings list.
        if "general" in parser and "visible_settings" in parser["general"]:
            visible_settings = set(parser["general"]["visible_settings"].split(";"))
            for removed in _REMOVED_SETTINGS:
                if removed in visible_settings:
                    visible_settings.remove(removed)

            parser["general"]["visible_settings"] = ";".join(visible_settings)

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades instance containers to remove the settings that were removed in this version.
        It also changes the instance containers to have the new version number.

        This removes any settings that were removed in the new Cura version and updates settings that need to be updated
        with a new value.

        :param serialized: The original contents of the instance container.
        :param filename: The original file name of the instance container.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "21"

        if "values" in parser:
            # Remove deleted settings from the instance containers.
            for removed in _REMOVED_SETTINGS:
                if removed in parser["values"]:
                    del parser["values"][removed]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades stacks to have the new version number.

        :param serialized: The original contents of the stack.
        :param filename: The original file name of the stack.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}

        parser["metadata"]["setting_version"] = "21"

        for container in parser['containers']:
            parser['containers'][container] = _RENAMED_PROFILES.get(parser['containers'][container], parser['containers'][container])

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
