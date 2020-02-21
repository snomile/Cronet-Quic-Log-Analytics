from datetime import datetime

event_type_dict = {}
source_type_dict = {}
phase_type_dict = {}
quic_rst_error_type_dict = {}
quic_error_type_dict = {}
basetime = 0

def revert_key_value(dict):
    return {v : k for k, v in dict.items()}

def init(constants_dict):
    global event_type_dict,source_type_dict,phase_type_dict,quic_rst_error_type_dict,quic_error_type_dict,basetime
    basetime = constants_dict['timeTickOffset']
    event_type_dict = revert_key_value(constants_dict['logEventTypes'])
    source_type_dict = revert_key_value(constants_dict['logSourceType'])
    phase_type_dict = revert_key_value(constants_dict['logEventPhase'])
    quic_rst_error_type_dict = revert_key_value(constants_dict['quicRstStreamError'])
    quic_error_type_dict = revert_key_value(constants_dict['quicError'])

def get_readable_time(time_offset):
    real_time_ms = basetime + time_offset
    local_dt_time = datetime.fromtimestamp(real_time_ms / 1000.0)
    local_str_time = local_dt_time.strftime("%y-%m-%d %H:%M:%S.%f")
    return local_str_time

def get_event_type(type_id):
    if event_type_dict:
        return event_type_dict[type_id]
    else:
        return type_id

def get_source_type(type_id):
    if source_type_dict:
        return source_type_dict[type_id]
    else:
        return type_id

def get_phase(phase_id):
    if phase_type_dict:
        return phase_type_dict[phase_id]
    else:
        return phase_id

def get_quic_rst_error(error_id):
    if quic_rst_error_type_dict:
        return quic_rst_error_type_dict[error_id]
    else:
        return error_id

def get_quic_error(error_id):
    return quic_error_type_dict[error_id]

def get_int_big_endian(big_endian_hex):
    if big_endian_hex:
        big_endian_hex = big_endian_hex.replace('0x', '')
        little_endian_hex = ''
        for i in range(0, len(big_endian_hex), 2):
            little_endian_hex = big_endian_hex[i: i + 2] + little_endian_hex

        return int(little_endian_hex, 16)
    else:
        return None

def find_key_value(shlo_str, key):
    value_str = find_key_value_str(shlo_str, key)
    return get_int_big_endian(value_str)

def find_key_value_str(shlo_str, key):
    key_value_str = shlo_str[shlo_str.find(key): shlo_str.find('\n', shlo_str.find(key))]
    if key_value_str:
        value_str = key_value_str.split(': ')[1]
        return value_str
    else:
        return None

if __name__ == '__main__':
    #print(find_key_value("REJ <\n  STK : 0x7ffcb26db3267f456ce78a277a966376848bde7ebf1b06c7d2f99d50f1b0f0ffe9c6a922e71525c5195fa026baf7c5cd0806d1deaa344c1e\n  SNO : 0xfdb66bf9b5f24cccfdc3f47a59e5fa371691ad34b3fce025135f26fab3ceda78a6dce6bedb73df0be005435df704d57b3a89f8f2\n  PROF: 0x3046022100caa55b9a02c419c6c35277dce81cfdca3a244fbdc01bba02e57902bf555b0b89022100ac66dc6fa184bafc3bdf89c3f861ca437c7ec460a840329c05e9db54f9af66ce\n  SCFG: \n    SCFG<\n      AEAD: 'AESG','CC20'\n      SCID: 0x01dc864f909a97590e3f14088382b3ff\n      PDMD: 'CHID'\n      PUBS: 0x200000db4a208eec135c320ff7017d64c5e2d45f3215a3657b4393817ccd472ed12703\n      KEXS: 'C255'\n      OBIT: 0x3030303030303030\n      EXPY: 0x60a8e45d00000000\n    >\n  RREJ: SERVER_CONFIG_INCHOATE_HELLO_FAILURE\n  STTL: 0x987d020000000000\n  CRT : 0x0101009f0d000078bb22517eb1ad577d3c94e91a1e638cc14cbe225f31426d64bc332115d556942589d6eab4c9981963cc78dfc9ccf8d8d559865494a365cb92668a8a428e551b511db5fa290eaa2545a9b643a988943ed479e61dc63bd6f9ed3fc71f66ae6b9ef779eef7beefe77aaec7570707944bc71b92929ce54083f07803db9e0bfd1fd684eb9070e06f6e860f5696f4802cad5657256bc84ad9ba26eb10842be04cf4a7a25820b1a2c9c6d2048db53918e83795be918eaac1525079376889ab3bdd1dec290604d1191e13108a545f63620e92b1ee1ad03891482ccc634e76a4b63165032281c58af60ae171e22707eb82059501f9fbafa19b40c6681464b22348aa8246abbb05d0dae0e5feed8507b2827ed1d4d0d65c8d23ac1d0a7dbb7e4fce1bc384b4772963f2128adbcac19457de3f1497155cca4d3ef4ba5456c22a7f553ab656f0e8655ba1454a5c8dfc9f79d9d70a93138478bd9573e02229b11b9212efa84b9476321a07503432a43ba568d3755075607485681d330cabc89297263406db94aeb071392d54ab745efb186c30d05af03c5c66966d291fd8a933ee04b131cd180a85400b30cd68896d46219f8766c3852b16d1113ae484e9479b8981536344b10c175043503fb4e1a4844245208604292117806ca95a6aa514471a1366c7223c360a4d01140a3930970773b0c38c1c692c012261633933c0c522f16ce5198dfd850896005fa4b3c0270b6ca6383103e50d51cc62c30a8a8e52ba80e20aa3c0c686d1e17c0e0b06118814d87432526726cc14248a792c11fa8cded41b30b14080ce3019068d07abe368a13a96f0a5fad85cd098b1d309c9342262fa08f092ea444cc234423cfd91381813339b83011c110644c6624094040378620c8005182054036245d59480c906f2a84c9e2a182503a3454189a9c4cf5651484c0c4751dcc9eaa16c1c8fcd41504ad14b22313847588ac72818a4ec99093835b3a2dcd8d24f7606583186238e054f626700d383d68ae2a11a2f35502001b6cf8c1d69f11c66ec9fba2611918825111c67186121089fa7eaf4097eb2d32720872d515aa3c9b79ce0f9e04041296d4089691168a94017c67051d642b56f043c0e2c166103d3c3ee294b36278e2340849c58d5569b1c0a4bad543f8a66f895806e23926a8790d5de94080602ab2a9d3de32ed1c5c4a33fbdc24633d4d76c6223ff390c5d4c1574d1c358b93009cd149a196c6a67cf9858fde969d542930ad92aed1738ff211291c84d2183d30d28ad2eea6c3a12f15a9aa8f3007ef10b683e642f9f27a7a65b63fca24af954a22700269f383501014f48794b48798d1bc6c5e3aaacb59a338fb56450037647be73aac970a072f977df0bfbaa7c839d0733b3c370380d78d9c54df7703882266e3de483b7c53d5dbaddebc201470fcdf8dadbf51747af3fbd14dd1047adb247fc178f38ae6c67802105dbff33d23cf0e51d7b0699baec7ea0ccdb41244991b9ee193ac8973425dd18070b879d14bd7b1072b9efacfbfa9d6dbebd8cef0ee493d38e1a19a599490ea6ecf00e552e1c340bb3f0c181bd014fdbb60fccaab70c9747d59844ddf87991ec808d779179b01dde0b1a024306ea9e45e41c2066cb777f99b6785fc2d5f9adefe55792aae29f9bfa94153bf3b8d35c017a45f28bfe7685454fd52a1292b84af7e3eff9493ec85b1f42dcceea74eb9e8adb465c9323db2273bb3b42cf15c326c3f9c70246e3b6e90f667e5d7b73dcf5b7b0b50dc3ada91f92fc2a29a30b1bf275e62cfab4e1d1de9a5745f236faf7fd7d91f992bc0477472bc313cd41e4c75cda379ef72f46f45e7ae287f8849f4b5b23bbda65ee74f6e8aee1e8b1ebc6e77725a6c69cb5f8497aa2e6b7bcc671fb2fba5213da479a70f2b4dbeb6a9b0e1f6f5b3470c16aef93f316dd52fdc8be215a41b74c6bdbada6decfce82790f4e65bef188dbdd30febed08e966b15de3bfa24f96256b7a8ceec9792a74f2a6887d973c72ac5655b1b83ccfee6575fd631a473bc4a2fa63346e8be3f6c57004161a6085f41524d86d24c51341e57e71fdd9f519ae2c00b3c3fdd49f9d3a990b5d2fbce99f2b9d42004112b8c92333588817533534e18e3a95424eaa99640ee7437c52dc595a1f054743a4305ff2fbeedafeebe6d66addeb7335b6e1dfe63d5e0dfab7b78b6964dad9e59fe921a7dba799ad711cf85838114831c442b3959e628af37f2c33ff492859ada7f82647ae2f8af73e6fabdddf0f047a9c19b4d65e42b55f372f55df97906be7d7a85a94b7ba88d56ce83ed664c4e9f5d2ab5c4cee8f34dfb1f6ebbf4ad8ddebaa13330b2f2cc91d52cad0fbd565759cc33b2e8c59f230ed5afefba95349bdb2de9a6f1fac76212786dbf1a689d7f456f586e3f6eb1583c66d7fb9c6f9e61daf8b8a5b845efde2fc55bc23df62c2f9f5bd3b8ef64b0e5c7baaee2d3753d9eccce1c93bc9729f5ff78c45e475d450ce82c3bd45f73798bd1515f07bb3f5e085d171daf6625bd2bf24a6d6f89b12fd3c66b6ae0348aa41a8b41465cd4ad9f46fa5f5d668d5426900411c1075e036b0567747a582b58f048fb1bae95f5e568e2fd2dd5f9ce0fbacdd369901bc60a2e8416400e182b683eb31504360f622875d10902cfc81de476e9b633e922ea0815ff50695ca9945b0fc81d7255c9edffb860aba6c05ea26650148be415ee891f4668a53e4b76866d3675abb81640faf9537dbb2b6f7e50a4b6976eadef8d88d7af2cb23e1a6e8c3ae82f76bac5bd5f55744a6b7fda067f2a47fff8c1bb14d331c1f27b08c16e0f7f99e05fe1f551b21d592f9d435db5877edffc347dcbf8f76114dbdcd17d4d25637786cb9bf52d46f24f961216bc2b6aaafc8c4fe0336bafb939f587bcdf78c58afce29c67b5dfb317cd0f3d9f7753f675ac28b8be3a34b3d9d476ceaaba631d918377af9a6c6dd97baa40677e1fe32605e652f15b0d2ab3750e936d8e94df59feece84741bfc1b7a420f34d8e3b2e947d77b6c7e4855313c9715146f509dbd3accf9d41be816d7b7f2d1f3ef321b0c2e5e14f94119ff2c2c3a3d7ff0b52ded328\n>",'STTL'))
    #print(get_int_big_endian('0x2988020000000000'))
    basetime = 1574569502250
    print(get_readable_time(1050366993))