import zipfile

def resore_file(zip_path):
    zip_package = zipfile.ZipFile(zip_path, "r")
    for filename in zip_package.namelist():
        print(filename)
        line = str(zip_package.read(filename), encoding="utf-8")
        print(line)

if __name__ == '__main__':
    zip_path = '/Users/zhangliang/PycharmProjects/chrome_quic_log_analytics/resource/data_original/netlog-1575619680.json.zip'
    resore_file(zip_path)