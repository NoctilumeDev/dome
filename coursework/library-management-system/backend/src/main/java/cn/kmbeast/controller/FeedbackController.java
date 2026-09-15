package cn.kmbeast.controller;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.FeedbackQueryDto;
import cn.kmbeast.pojo.entity.Feedback;
import cn.kmbeast.pojo.vo.FeedbackVO;
import cn.kmbeast.service.FeedbackService;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

@RestController
@RequestMapping("/feedback")
public class FeedbackController {
    @Resource
    private FeedbackService feedbackService;

    @PostMapping("/submit")
    public Result<Void> submit(@RequestBody Feedback feedback) {
        return feedbackService.submit(feedback);
    }

    @PostMapping("/mine")
    public Result<List<FeedbackVO>> queryMine(@RequestBody FeedbackQueryDto dto) {
        return feedbackService.queryMine(dto);
    }

    @PostMapping("/query")
    public Result<List<FeedbackVO>> query(@RequestBody FeedbackQueryDto dto) {
        return feedbackService.query(dto);
    }

    @PutMapping("/reply")
    public Result<Void> reply(@RequestBody Feedback feedback) {
        return feedbackService.reply(feedback);
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Integer id) {
        return feedbackService.delete(id);
    }
}
