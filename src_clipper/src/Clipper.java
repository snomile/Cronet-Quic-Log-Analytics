import java.io.*;
import java.util.regex.Pattern;

public class Clipper {

    private static Pattern pn_10 = Pattern.compile(".*source\":\\{\"id\":[0-9]*,\"type\":10.*");
    private static Pattern pn_13 = Pattern.compile(".*source\":\\{\"id\":[0-9]*,\"type\":13.*");

    public void clip(String origin_file_path, boolean keep_non_essential, boolean replace_original_file){
        try{
            File origin_file = new File(origin_file_path);
            String tmp_file_path = origin_file_path + "_tmp";
            File tmp_file = new File(tmp_file_path);

            InputStreamReader Stream=new InputStreamReader(new FileInputStream(origin_file),"UTF-8");
            BufferedReader reader=new BufferedReader(Stream);

            OutputStreamWriter outStream=new OutputStreamWriter(new FileOutputStream(tmp_file),"UTF-8");
            BufferedWriter writer=new BufferedWriter(outStream);

            String line=null;
            while((line=reader.readLine())!=null)
            {
                if(line.contains("{\"constants\":{\""))
                {
                    writer.write("{");
                }
                else if (line.equals("\"events\": [") || keep_non_essential || pn_10.matcher(line).find() || pn_13.matcher(line).find()) {  // "HOST_RESOLVER_IMPL_JOB":13,"QUIC_SESSION":10
                    writer.write(line + "\r\n");
                }
            }

            reader.close();
            writer.close();

            if (replace_original_file){
                origin_file.delete();
                tmp_file.renameTo(origin_file);
            }
        }
        catch(Exception e){
            e.printStackTrace(); //TODO 在安卓上需要修改，例如直接上传未处理的原始文件，以备进一步检查文件错误
        }
    }

    public static void main(String[] args) {
        Clipper clipper = new Clipper();
        clipper.clip("/Users/zhangliang/PycharmProjects/chrome_quic_log_analytics/resource/data_original/netlog-1575101576.json", false, false);
    }

}
