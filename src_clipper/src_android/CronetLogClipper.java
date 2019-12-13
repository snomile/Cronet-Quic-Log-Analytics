import android.content.Context;
import android.util.Log;

import com.star.util.Logger;
import com.star.util.ThreadPoolManager;

import java.io.*;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class CronetLogClipper {
    private static final int save_batch = 500;
    private static final int expect_average_row_length = 220;

    private static final Pattern source_quic_session = Pattern.compile(".*e\":10.*"); // "QUIC_SESSION":10
    private static final Pattern source_host_resolver = Pattern.compile(".*e\":13.*"); // "HOST_RESOLVER_IMPL_JOB":13
    private static final Pattern event_type_236 = Pattern.compile(".*236.*"); //"QUIC_SESSION_CERTIFICATE_VERIFIED":236,
    private static final Pattern event_type_242 = Pattern.compile(".*242.*"); //"QUIC_SESSION_UNAUTHENTICATED_PACKET_HEADER_RECEIVED":242,
    private static final Pattern event_type_243 = Pattern.compile(".*243.*"); //"QUIC_SESSION_PACKET_AUTHENTICATED":243
    private static final Pattern event_type_266 = Pattern.compile(".*266.*"); //"QUIC_SESSION_VERSION_NEGOTIATED":266,
    private static final Pattern event_type_285 = Pattern.compile(".*285.*"); //"QUIC_SESSION_PADDING_FRAME_SENT":285
    private static final Pattern event_type_286 = Pattern.compile(".*286.*"); //"QUIC_SESSION_PADDING_FRAME_RECEIVED":286,
    private static final Pattern event_type_355 = Pattern.compile(".*355.*"); //"CERT_VERIFIER_REQUEST":355,
    private static final Pattern event_type_357 = Pattern.compile(".*357.*"); //"CERT_VERIFIER_REQUEST_BOUND_TO_JOB":357,


    private String getBaseTime(String line, int length){
        int time_base_index = line.lastIndexOf("\"timeTickOffset",length);
        return line.substring(time_base_index, line.length()-2);
    }

    private String getPacketNumber(String line){
        int packet_number_index = line.lastIndexOf("\"packet_number\"");
        int next_comma_index = line.indexOf(",", packet_number_index);
        return line.substring(packet_number_index, next_comma_index);
    }

    public ClipperResult clip(String origin_file_path, boolean keep_all, boolean keep_constants, boolean keep_all_quic){
        ClipperResult result = new ClipperResult();
        try{
            File origin_file = new File(origin_file_path);
            String tmp_file_path = origin_file_path + ".zip";
            File zip_file = new File(tmp_file_path);

            InputStreamReader input = new InputStreamReader(new FileInputStream(origin_file),"UTF-8");
            BufferedReader reader=new BufferedReader(input);
            ZipOutputStream zipOut = new ZipOutputStream(new FileOutputStream(zip_file));
            zipOut.putNextEntry(new ZipEntry(origin_file.getName()));

            String line;
            boolean has_constants = true;
            int cache_line_counter = 0;
            StringBuilder write_cache = new StringBuilder(save_batch * expect_average_row_length);
            String event_type_part ;
            String source_part;
            int line_length;
            result.setFilelen((int)origin_file.length());
            try{
                while((line=reader.readLine())!=null)
                {
                    line_length = line.length();
                    cache_line_counter++;
                    if (keep_all){
                        write_cache.append(line);
                    }
                    else if(has_constants && line.startsWith("{\"constants\":{\"")) {  //filter constants
                        has_constants = false; //save processor power by avoiding repeatly enter this section
                        if (!keep_constants) {
                            String base_time = getBaseTime(line, line_length);
                            write_cache.append("{" + base_time + ",\"events\": [\n");
                        } else {
                            write_cache.append(line);
                        }
                    } else{
                        source_part = line.substring(Math.max(0, line_length-60),Math.max(0, line_length-30));
                        if (source_quic_session.matcher(source_part).find() || source_host_resolver.matcher(source_part).find()) {  //filter quic events
                            if (keep_all_quic) {
                                write_cache.append(line);
                            }else{
                                event_type_part = line.substring(line_length-5);
                                if (event_type_236.matcher(event_type_part).find() ||
                                        event_type_243.matcher(event_type_part).find() ||
                                        event_type_266.matcher(event_type_part).find() ||
                                        event_type_285.matcher(event_type_part).find() ||
                                        event_type_286.matcher(event_type_part).find() ||
                                        event_type_355.matcher(event_type_part).find() ||
                                        event_type_357.matcher(event_type_part).find()
                                ){
                                    continue;
                                }
//                            else if (event_type_242.matcher(event_type_part).find()){
//                                write_cache.append(getPacketNumber(line));
//                            }
                                else{
                                    write_cache.append(line);
                                    write_cache.append('\n');
                                }
                            }
                        }
                    }

                    if (cache_line_counter > save_batch){
                        zipOut.write((write_cache.toString()).getBytes("UTF-8"));
                        write_cache.delete( 0, write_cache.length() );
                    }
                }
                zipOut.write((write_cache.toString()).getBytes("UTF-8"));
                reader.close();
                zipOut.close();
            }catch (Exception ex){
                Logger.e("clip log excption, log="+origin_file_path+", ex="+ex.getMessage());
                result.setError(ex.getMessage());
                result.setRet(CLIPERR_CLIPFAIL);
                zip_file.delete();
                cutFile(result.getFilelen(), origin_file_path);
            }
        }
        catch(Exception ex){
            result.setError(ex.getMessage());
            result.setRet(CLIPERR_FILEIO);
        }
        return result;
    }

    private void cutFile(int filelen, String origin_file_path) throws IOException{
        if (filelen>2048){
            File origin_file = new File(origin_file_path);
            String tmp_file_path = origin_file_path + ".zip";
            File zip_file = new File(tmp_file_path);
            InputStreamReader input = new InputStreamReader(new FileInputStream(origin_file),"UTF-8");
            BufferedReader reader=new BufferedReader(input);
            ZipOutputStream zipOut = new ZipOutputStream(new FileOutputStream(zip_file));
            zipOut.putNextEntry(new ZipEntry(origin_file.getName()));

            String useful_cache = "";
            input.reset();
            char [] headData = new char[256];
            char [] tailData = new char[1024];
            input.read(headData,0, headData.length);
            input.read(tailData, filelen-1024, 1024);
            useful_cache += headData;
            useful_cache += "*****************";
            useful_cache += tailData;
            zipOut.write(useful_cache.getBytes("UTF-8"));
            zipOut.close();
            input.close();
        }
    }

    public interface ClipperCallback{
        void onClipper(ClipperResult result, byte[] logFile);
    }


    public static final int CLIPERR_FILEIO     = -1;
    public static final int CLIPERR_CLIPFAIL   = -2;
    public static final int CLIPERR_NO_DATA    = -3;
    public static final int CLIPERR_UNKNOWN    = -4;

    public static class ClipperResult{
        private int ret;
        private String error = "";
        private int fileLen;
        ClipperResult(int ret, String err, int len){
            this.ret = ret;
            this.error = err;
            this.fileLen = len;
        }

        ClipperResult(){

        }

        public int getRet() {
            return ret;
        }

        public void setRet(int ret) {
            this.ret = ret;
        }

        public String getError() {
            return error;
        }

        public void setError(String error) {
            this.error = error;
        }

        public int getFilelen() {
            return fileLen;
        }

        public void setFilelen(int len) {
            this.fileLen = len;
        }
    }
}
