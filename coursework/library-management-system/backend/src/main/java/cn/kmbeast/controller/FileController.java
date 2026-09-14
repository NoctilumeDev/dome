package cn.kmbeast.controller;

import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.utils.IdFactoryUtil;
import cn.kmbeast.utils.PathUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletResponse;
import javax.validation.constraints.NotNull;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * 文件前端控制器
 *
 * @since 2024-03-22
 */
@RestController
@RequestMapping("/file")
public class FileController {

    @Value("${my-server.api-context-path}")
    private String API;

    @Value("${file.upload-dir:./upload/pic}")
    private String uploadDir;

    /** 允许的文件扩展名白名单 */
    private static final Set<String> ALLOWED_EXTENSIONS = new HashSet<>(Arrays.asList(
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
            ".mp4", ".avi", ".mov", ".wmv",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"
    ));

    /** 扩展名到 MIME 类型的映射 */
    private static final Map<String, String> MIME_TYPES = new HashMap<>();
    static {
        MIME_TYPES.put(".jpg", "image/jpeg");
        MIME_TYPES.put(".jpeg", "image/jpeg");
        MIME_TYPES.put(".png", "image/png");
        MIME_TYPES.put(".gif", "image/gif");
        MIME_TYPES.put(".bmp", "image/bmp");
        MIME_TYPES.put(".webp", "image/webp");
        MIME_TYPES.put(".mp4", "video/mp4");
        MIME_TYPES.put(".avi", "video/x-msvideo");
        MIME_TYPES.put(".mov", "video/quicktime");
        MIME_TYPES.put(".wmv", "video/x-ms-wmv");
        MIME_TYPES.put(".pdf", "application/pdf");
        MIME_TYPES.put(".doc", "application/msword");
        MIME_TYPES.put(".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
        MIME_TYPES.put(".xls", "application/vnd.ms-excel");
        MIME_TYPES.put(".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        MIME_TYPES.put(".ppt", "application/vnd.ms-powerpoint");
        MIME_TYPES.put(".pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation");
    }

    /**
     * 文件上传
     */
    @PostMapping("/upload")
    public Result<String> uploadFile(@RequestParam("file") MultipartFile multipartFile) {
        return doUpload(multipartFile);
    }

    /**
     * 视频上传
     */
    @PostMapping("/video/upload")
    public Result<String> videoUpload(@RequestParam("file") MultipartFile multipartFile) {
        return doUpload(multipartFile);
    }

    /**
     * 统一上传逻辑
     */
    private Result<String> doUpload(MultipartFile multipartFile) {
        String originalFilename = multipartFile.getOriginalFilename();
        if (originalFilename == null || !originalFilename.contains(".")) {
            return ApiResult.error("文件类型不支持");
        }
        String extension = originalFilename.substring(originalFilename.lastIndexOf(".")).toLowerCase();
        if (!ALLOWED_EXTENSIONS.contains(extension)) {
            return ApiResult.error("不支持的文件类型: " + extension);
        }
        String uuid = IdFactoryUtil.getFileId();
        String fileName = uuid + extension;
        try {
            if (saveFile(multipartFile, fileName)) {
                return ApiResult.success(API + "/file/getFile?fileName=" + fileName);
            }
        } catch (IOException e) {
            return ApiResult.error("文件上传异常");
        }
        return ApiResult.error("文件上传异常");
    }

    /**
     * 保存文件到磁盘
     */
    public boolean saveFile(MultipartFile multipartFile, String fileName) throws IOException {
        File fileDir = new File(uploadDir);
        if (!fileDir.exists()) {
            if (!fileDir.mkdirs()) {
                return false;
            }
        }
        File file = new File(fileDir.getAbsolutePath() + File.separator + fileName);
        if (file.exists()) {
            if (!file.delete()) {
                return false;
            }
        }
        if (file.createNewFile()) {
            multipartFile.transferTo(file);
            return true;
        }
        return false;
    }

    /**
     * 查看文件资源
     */
    @GetMapping("/getFile")
    public void getFile(@RequestParam("fileName") String fileName,
                        HttpServletResponse response) throws IOException {
        // 路径遍历防护
        if (fileName.contains("..") || fileName.contains("/") || fileName.contains("\\")) {
            response.setStatus(400);
            return;
        }
        File fileDir = new File(uploadDir);
        File file = new File(fileDir.getAbsolutePath() + File.separator + fileName);
        if (file.exists()) {
            // 设置 Content-Type
            String extension = "";
            int dotIndex = fileName.lastIndexOf(".");
            if (dotIndex > 0) {
                extension = fileName.substring(dotIndex).toLowerCase();
            }
            String contentType = MIME_TYPES.getOrDefault(extension, "application/octet-stream");
            response.setContentType(contentType);

            try (FileInputStream fileInputStream = new FileInputStream(file);
                 OutputStream outputStream = response.getOutputStream()) {
                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = fileInputStream.read(buffer)) != -1) {
                    outputStream.write(buffer, 0, bytesRead);
                }
                outputStream.flush();
            }
        } else {
            response.setStatus(404);
        }
    }
}