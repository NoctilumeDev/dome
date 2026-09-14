package cn.kmbeast.controller;

import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.extend.UserQueryDto;
import cn.kmbeast.pojo.dto.update.UserLoginDTO;
import cn.kmbeast.pojo.dto.update.UserRegisterDTO;
import cn.kmbeast.pojo.dto.update.UserUpdateDTO;
import cn.kmbeast.pojo.entity.User;
import cn.kmbeast.pojo.vo.ChartVO;
import cn.kmbeast.pojo.vo.UserVO;
import cn.kmbeast.service.UserService;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.List;
import java.util.Map;

/**
 * 用户控制器
 */
@RestController
@RequestMapping("/user")
public class UserController {

    @Resource
    private UserService userService;

    /**
     * 用户登录
     */
    @PostMapping(value = "/login")
    @ResponseBody
    public Result<Object> login(@Valid @RequestBody UserLoginDTO userLoginDTO) {
        return userService.login(userLoginDTO);
    }

    /**
     * token校验
     */
    @GetMapping(value = "/auth")
    @ResponseBody
    public Result<UserVO> auth() {
        return userService.auth();
    }

    /**
     * 通过ID查询用户信息
     */
    @GetMapping(value = "/getById/{id}")
    @ResponseBody
    public Result<UserVO> getById(@PathVariable Integer id) {
        return userService.getById(id);
    }

    /**
     * 用户注册
     */
    @PostMapping(value = "/register")
    @ResponseBody
    public Result<String> register(@Valid @RequestBody UserRegisterDTO userRegisterDTO) {
        return userService.register(userRegisterDTO);
    }

    /**
     * 用户信息修改
     */
    @PutMapping(value = "/update")
    @ResponseBody
    public Result<String> update(@Valid @RequestBody UserUpdateDTO userUpdateDTO) {
        return userService.update(userUpdateDTO);
    }

    /**
     * 后台用户信息修改
     */
    @PutMapping(value = "/backUpdate")
    @ResponseBody
    public Result<String> backUpdate(@RequestBody User user) {
        return userService.backUpdate(user);
    }

    /**
     * 用户修改密码
     */
    @PutMapping(value = "/updatePwd")
    @ResponseBody
    public Result<String> updatePwd(@RequestBody Map<String, String> map) {
        return userService.updatePwd(map);
    }

    /**
     * 批量删除用户信息
     */
    @PostMapping(value = "/batchDelete")
    @ResponseBody
    public Result<String> batchDelete(@RequestBody List<Integer> ids) {
        return userService.batchDelete(ids);
    }

    /**
     * 冻结用户
     */
    @PutMapping(value = "/freeze/{id}")
    @ResponseBody
    public Result<String> freezeUser(@PathVariable Integer id) {
        return userService.freezeUser(id);
    }

    /**
     * 解冻用户
     */
    @PutMapping(value = "/unfreeze/{id}")
    @ResponseBody
    public Result<String> unfreezeUser(@PathVariable Integer id) {
        return userService.unfreezeUser(id);
    }

    /**
     * 查询用户数据
     */
    @PostMapping(value = "/query")
    @ResponseBody
    public Result<List<User>> query(@RequestBody UserQueryDto userQueryDto) {
        return userService.query(userQueryDto);
    }

    /**
     * 后台新增用户
     */
    @PostMapping(value = "/insert")
    @ResponseBody
    public Result<String> insert(@Valid @RequestBody UserRegisterDTO userRegisterDTO) {
        return userService.insert(userRegisterDTO);
    }

    /**
     * 统计用户存量数据
     */
    @GetMapping(value = "/daysQuery/{day}")
    @ResponseBody
    public Result<List<ChartVO>> query(@PathVariable Integer day) {
        return userService.daysQuery(day);
    }
}
