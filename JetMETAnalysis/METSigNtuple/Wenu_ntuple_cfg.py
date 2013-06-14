import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

options = VarParsing ('analysis')

options.setDefault( 'outputFile',
      'ntuple.root'
      )

options.register( 'globalTag',
      'START53_V7A',
      VarParsing.multiplicity.singleton,
      VarParsing.varType.string,
      "CMS Global Tag"
      )

options.register( 'runOnMC',
      False,
      VarParsing.multiplicity.singleton,
      VarParsing.varType.bool,
      "True for MC"
      )

options.parseArguments()

process = cms.Process("Demo")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(options.maxEvents) )

process.source = cms.Source("PoolSource",
      fileNames = cms.untracked.vstring(
         '/store/mc/Summer12_DR53X/WJetsToLNu_TuneZ2Star_8TeV-madgraph-tarball/AODSIM/PU_S10_START53_V7A-v2/0000/000869F4-59EE-E111-9BF6-003048D47752.root'
         #'/store/data/Run2012A/SingleElectron/AOD/13Jul2012-v1/0000/001A2EB8-47D4-E111-B527-003048679070.root'
         )
      )

process.load("Configuration.StandardSequences.Geometry_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
process.GlobalTag.globaltag = ( options.globalTag+'::All' )
process.load("JetMETCorrections.Configuration.DefaultJEC_cff")

process.load("CommonTools.ParticleFlow.PF2PAT_cff")
process.pfPileUp.Enable = False

process.pfAllMuons.src="particleFlow"
process.pfMuonsFromVertex.dzCut=9999
process.pfNoMuon.bottomCollection   = "particleFlow"
#process.pfNoMuon.topCollection      = "pfSelectedMuons"
process.pfJets.doAreaFastjet        = True
process.pfJets.jetPtMin             = 0
process.pfJets.src                  = "pfNoElectron"

#process.pfAllNeutralHadrons.src = "particleFlow"
#process.pfAllChargedHadrons.src = "particleFlow"
#process.pfAllPhotons.src = "particleFlow"
#process.pfAllChargedParticles.src = "particleFlow"
#process.pfAllNeutralHadronsAndPhotons.src = "particleFlow"

#process.pfSortByTypeSequence.remove( process.pfPileUpAllChargedParticles )

process.load("RecoJets.JetProducers.ak5PFJets_cfi")
process.ak5PFJets.doAreaFastjet = cms.bool(True)

process.mypf2pat = cms.Sequence(
      #process.pfSortByTypeSequence *
      process.pfNoPileUpSequence *
      process.pfParticleSelectionSequence *
      #process.pfAllMuons * 
      #process.pfMuonsFromVertex *
      #process.pfSelectedMuons *
      process.pfMuonSequence *
      process.pfNoMuon *
      process.pfElectronSequence *
      process.pfNoElectron *
      process.pfJets
      )

# met corrections and filters
process.load("JetMETCorrections.Type1MET.pfMETCorrections_cff")
process.load("JetMETCorrections.Type1MET.pfMETsysShiftCorrections_cfi")

if options.runOnMC :
   process.pfMEtSysShiftCorr.parameter = process.pfMEtSysShiftCorrParameters_2012runAvsNvtx_mc
else :
   process.pfMEtSysShiftCorr.parameter = process.pfMEtSysShiftCorrParameters_2012runAvsNvtx_data

process.pfType1CorrectedMet.srcType1Corrections = cms.VInputTag(
      cms.InputTag('pfJetMETcorr', 'type1') ,
      cms.InputTag('pfMEtSysShiftCorr')  
      )
process.pfType1p2CorrectedMet.srcType1Corrections = cms.VInputTag(
      cms.InputTag('pfJetMETcorr', 'type1') ,
      cms.InputTag('pfMEtSysShiftCorr')       
      )

process.mymet = cms.Sequence(
      process.pfMET *
      process.pfMEtSysShiftCorrSequence *
      process.producePFMETCorrections
      )

metList = []
metList.append(cms.untracked.InputTag("pfMet", "", ""))

# jet pileup id
from CMGTools.External.pujetidsequence_cff import puJetId, puJetMva

process.recoPuJetId = puJetId.clone(
      jets = cms.InputTag("pfJets"),
      applyJec = cms.bool(True),
      inputIsCorrected = cms.bool(False),                
      )

process.recoPuJetMva = puJetMva.clone(
      jets = cms.InputTag("pfJets"),
      jetids = cms.InputTag("recoPuJetId"),
      applyJec = cms.bool(True),
      inputIsCorrected = cms.bool(False),                
      )

process.recoPuJetIdSequence = cms.Sequence(process.recoPuJetId * process.recoPuJetMva )

# rho value for isolation
from RecoJets.JetProducers.kt4PFJets_cfi import *
process.kt6PFJetsForIsolation = kt4PFJets.clone( rParam = 0.6, doRhoFastjet = True )
process.kt6PFJetsForIsolation.Rho_EtaMax = cms.double(2.5)

# particle flow isolation
from CommonTools.ParticleFlow.Tools.pfIsolation import setupPFElectronIso, setupPFMuonIso
process.eleIsoSequence = setupPFElectronIso(process, 'gsfElectrons')
process.pfiso = cms.Sequence(process.pfParticleSelectionSequence + process.eleIsoSequence)

#trigger_paths = ["HLT_Ele22_CaloIdL_CaloIsoVL_v"]
trigger_paths = ["HLT_Ele27_WP80_v"]
trigger_pattern = [path+"*" for path in trigger_paths]

process.demo = cms.EDAnalyzer('METSigNtuple',
      runOnMC              = cms.untracked.bool(options.runOnMC),
      output_file          = cms.untracked.string(options.outputFile),

      saveJetInfo          = cms.untracked.bool(False),

      selectionChannel     = cms.untracked.string('Wenu'),

      pfjetsTag            = cms.untracked.InputTag('pfJets'),
      pfjetCorrectorL1     = cms.untracked.string('ak5PFL1Fastjet'),
      pfjetCorrectorL123   = cms.untracked.string('ak5PFL1FastL2L3'),
      jetResAlgo           = cms.string('AK5PF'),
      jetResEra            = cms.string('Spring10'),

      muonTag              = cms.untracked.InputTag("pfIsolatedMuons"),
      electronTag          = cms.untracked.InputTag("pfIsolatedElectrons"),

      conversionsInputTag     = cms.InputTag("allConversions"),
      rhoIsoInputTag          = cms.InputTag("kt6PFJetsForIsolation", "rho"),
      isoValInputTags         = cms.VInputTag(cms.InputTag('elPFIsoValueCharged03PFIdPFIso'),
         cms.InputTag('elPFIsoValueGamma03PFIdPFIso'),
         cms.InputTag('elPFIsoValueNeutral03PFIdPFIso')),

      genparticlesTag      = cms.untracked.InputTag("genParticles"),
      pfcandidatesTag      = cms.untracked.InputTag("particleFlow"),

      genjetsTag           = cms.untracked.InputTag('ak5GenJets'),

      metsTag              = cms.untracked.VInputTag(metList),
      genmetTag            = cms.untracked.InputTag('genMetCalo'),

      verticesTag          = cms.untracked.InputTag('offlinePrimaryVertices'),
      pileupTag            = cms.untracked.InputTag('addPileupInfo')
      )
if not options.runOnMC:
   process.demo.pfjetCorrectorL123 = 'ak5PFL1FastL2L3Residual'

# MET filters for ICHEP 2012
# obtained from
# https://twiki.cern.ch/twiki/bin/view/CMS/MissingETOptionalFilters#A_Central_Filter_Package_RecoMET

#from PhysicsTools.PatAlgos.patTemplate_cfg import *
## The good primary vertex filter ____________________________________________||

process.primaryVertexFilter = cms.EDFilter(
      "VertexSelector",
      src = cms.InputTag("offlinePrimaryVertices"),
      cut = cms.string("!isFake && ndof > 4 && abs(z) <= 24 && position.Rho <= 2"),
      filter = cms.bool(True)
      )

## The beam scraping filter __________________________________________________||
process.noscraping = cms.EDFilter(
      "FilterOutScraping",
      applyfilter = cms.untracked.bool(True),
      debugOn = cms.untracked.bool(False),
      numtrack = cms.untracked.uint32(10),
      thresh = cms.untracked.double(0.25)
      )

## The iso-based HBHE noise filter ___________________________________________||
process.load('CommonTools.RecoAlgos.HBHENoiseFilter_cfi')

## The CSC beam halo tight filter ____________________________________________||
process.load('RecoMET.METAnalyzers.CSCHaloFilter_cfi')

## The HCAL laser filter _____________________________________________________||
process.load("RecoMET.METFilters.hcalLaserEventFilter_cfi")

## The ECAL dead cell trigger primitive filter _______________________________||
process.load('RecoMET.METFilters.EcalDeadCellTriggerPrimitiveFilter_cfi')

## The EE bad SuperCrystal filter ____________________________________________||
process.load('RecoMET.METFilters.eeBadScFilter_cfi')

## The ECAL laser correction filter
process.load('RecoMET.METFilters.ecalLaserCorrFilter_cfi')
#process.MessageLogger.suppressError = cms.untracked.vstring ('ecalLaserCorrFilter')

## The Good vertices collection needed by the tracking failure filter ________||
process.goodVertices = cms.EDFilter(
      "VertexSelector",
      filter = cms.bool(False),
      src = cms.InputTag("offlinePrimaryVertices"),
      cut = cms.string("!isFake && ndof > 4 && abs(z) <= 24 && position.rho < 2")
      )

## The tracking failure filter _______________________________________________||
process.load('RecoMET.METFilters.trackingFailureFilter_cfi')

## The tracking POG filters __________________________________________________||
process.load('RecoMET.METFilters.trackingPOGFilters_cff')

process.filtersSeq = cms.Sequence(
      process.primaryVertexFilter *
      process.noscraping *
      process.HBHENoiseFilter *
      process.CSCTightHaloFilter *
      process.hcalLaserEventFilter *
      process.EcalDeadCellTriggerPrimitiveFilter *
      process.goodVertices * process.trackingFailureFilter *
      process.eeBadScFilter *
      process.ecalLaserCorrFilter *
      process.trkPOGFilters
      )

# trigger filter                
from HLTrigger.HLTfilters.hltHighLevel_cfi import *
process.triggerSelection = hltHighLevel.clone(
      TriggerResultsTag = "TriggerResults::HLT",
      HLTPaths = trigger_pattern,
      throw=False
      )

process.p = cms.Path(
      process.triggerSelection *
      process.filtersSeq *
      process.mypf2pat *
      process.mymet *
      process.recoPuJetIdSequence *
      process.kt6PFJetsForIsolation *
      process.eleIsoSequence *
      process.pfiso *
      process.demo
      )
if options.runOnMC :
   process.p.remove( process.filtersSeq )

#process.out = cms.OutputModule( "PoolOutputModule"
#      , fileName = cms.untracked.string( "patTuple.root" )
#      )
#process.outpath = cms.EndPath( process.out )