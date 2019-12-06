import java.io.*;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class Clipper {

    private static Pattern pn_10 = Pattern.compile(".*source\":\\{\"id\":[0-9]*,\"type\":10.*");
    private static Pattern pn_13 = Pattern.compile(".*source\":\\{\"id\":[0-9]*,\"type\":13.*");

    private String getBaseTime(String line){
        int time_base_index = line.lastIndexOf("\"timeTickOffset");
        return line.substring(time_base_index, line.length()-2);
    }


    public void clip(String origin_file_path, boolean keep_non_essential){
        try{
            File origin_file = new File(origin_file_path);
            String tmp_file_path = origin_file_path + ".zip";
            File zip_file = new File(tmp_file_path);

            InputStreamReader input = new InputStreamReader(new FileInputStream(origin_file),"UTF-8");
            BufferedReader reader=new BufferedReader(input);
            ZipOutputStream zipOut = new ZipOutputStream(new FileOutputStream(zip_file));
            zipOut.putNextEntry(new ZipEntry(origin_file.getName()));

            String line=null;
            while((line=reader.readLine())!=null)
            {
                if(line.contains("{\"constants\":{\""))
                {
                    String base_time = getBaseTime(line);
                    String base_time_json = "{" + base_time + ',';
                    zipOut.write(base_time_json.getBytes("UTF-8"));
                }
                else if (line.equals("\"events\": [") || keep_non_essential || pn_10.matcher(line).find() || pn_13.matcher(line).find()) {  // "HOST_RESOLVER_IMPL_JOB":13,"QUIC_SESSION":10
                    zipOut.write( (line + "\r\n").getBytes("UTF-8"));
                }
            }

            reader.close();
            zipOut.close();
        }
        catch(Exception e){
            e.printStackTrace(); //TODO 在安卓上需要修改，例如直接将原始文件压缩上传，以备进一步检查文件错误
        }
    }

    public static void main(String[] args) {
        Clipper clipper = new Clipper();
        clipper.clip("/Users/zhangliang/PycharmProjects/chrome_quic_log_analytics/resource/data_original/netlog-1575619680.json", false);
    }

}
