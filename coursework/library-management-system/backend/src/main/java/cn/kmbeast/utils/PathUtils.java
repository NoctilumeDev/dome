package cn.kmbeast.utils;

import java.io.File;
import java.nio.file.Paths;

/**
 * 路径工具类，兼容 jar 包和 IDE 运行
 */
public class PathUtils {

    /**
     * 获取项目根路径
     */
    public static String getClassLoadRootPath() {
        // 优先使用 user.dir（兼容 jar 包运行）
        String userDir = System.getProperty("user.dir");
        if (userDir != null) {
            return userDir;
        }
        // 回退到 classpath 路径
        try {
            String path = PathUtils.class.getClassLoader().getResource("").getPath();
            if (path != null) {
                return Paths.get(path).toAbsolutePath().toString();
            }
        } catch (Exception ignored) {
        }
        return ".";
    }

    /**
     * 获取文件上传目录
     */
    public static String getUploadDir() {
        String dir = getClassLoadRootPath() + File.separator + "upload" + File.separator + "pic";
        File file = new File(dir);
        if (!file.exists()) {
            file.mkdirs();
        }
        return dir;
    }
}