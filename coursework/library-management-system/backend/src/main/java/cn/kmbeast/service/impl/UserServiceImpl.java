package cn.kmbeast.service.impl;

import cn.kmbeast.context.LocalThreadHolder;
import cn.kmbeast.mapper.UserMapper;
import cn.kmbeast.pojo.api.ApiResult;
import cn.kmbeast.pojo.api.PageResult;
import cn.kmbeast.pojo.api.Result;
import cn.kmbeast.pojo.dto.query.base.QueryDto;
import cn.kmbeast.pojo.dto.query.extend.UserQueryDto;
import cn.kmbeast.pojo.dto.update.UserLoginDTO;
import cn.kmbeast.pojo.dto.update.UserRegisterDTO;
import cn.kmbeast.pojo.dto.update.UserUpdateDTO;
import cn.kmbeast.pojo.em.LoginStatusEnum;
import cn.kmbeast.pojo.em.RoleEnum;
import cn.kmbeast.pojo.entity.User;
import cn.kmbeast.pojo.vo.ChartVO;
import cn.kmbeast.pojo.vo.UserVO;
import cn.kmbeast.service.UserService;
import cn.kmbeast.utils.DateUtil;
import cn.kmbeast.utils.JwtUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 用户服务实现类
 */
@Service
@Slf4j
public class UserServiceImpl implements UserService {

    @Resource
    private UserMapper userMapper;

    /**
     * 密码加密器（BCrypt 加盐哈希，工业标准，禁止明文存储）
     */
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    /**
     * 用户注册
     */
    @Override
    public Result<String> register(UserRegisterDTO userRegisterDTO) {
        // 密码强度校验（最少6位）
        if (userRegisterDTO.getUserPwd() == null || userRegisterDTO.getUserPwd().length() < 6) {
            return ApiResult.error("密码长度不能少于6位");
        }
        // 检查用户名重复
        User user = userMapper.getByActive(
                User.builder().userName(userRegisterDTO.getUserName()).build()
        );
        if (Objects.nonNull(user)) {
            return ApiResult.error("用户名已经被使用，请换一个");
        }
        // 检查账号重复
        User entity = userMapper.getByActive(
                User.builder().userAccount(userRegisterDTO.getUserAccount()).build()
        );
        if (Objects.nonNull(entity)) {
            return ApiResult.error("账号不可用");
        }
        User saveEntity = User.builder()
                .userRole(RoleEnum.READER.getRole())
                .userName(userRegisterDTO.getUserName())
                .userAccount(userRegisterDTO.getUserAccount())
                .userAvatar(userRegisterDTO.getUserAvatar())
                .userPwd(passwordEncoder.encode(userRegisterDTO.getUserPwd()))
                .createTime(LocalDateTime.now())
                .isLogin(LoginStatusEnum.USE.getFlag()).build();
        userMapper.insert(saveEntity);
        return ApiResult.success("注册成功");
    }

    /**
     * 用户登录
     */
    @Override
    public Result<Object> login(UserLoginDTO userLoginDTO) {
        User user = userMapper.getByActive(
                User.builder().userAccount(userLoginDTO.getUserAccount()).build()
        );
        if (!Objects.nonNull(user)) {
            return ApiResult.error("账号不存在");
        }
        // 检查账户是否被禁用
        if (user.getIsLogin() != null && user.getIsLogin()) {
            return ApiResult.error("账户已被禁用，请联系管理员");
        }
        // BCrypt 密码比对（数据库中必须是 BCrypt 哈希）
        if (!passwordEncoder.matches(userLoginDTO.getUserPwd(), user.getUserPwd())) {
            return ApiResult.error("密码错误");
        }
        String token = JwtUtil.toToken(user.getId(), user.getUserRole());
        Map<String, Object> map = new HashMap<>();
        map.put("token", token);
        map.put("role", user.getUserRole());
        return ApiResult.success("登录成功", map);
    }

    /**
     * 令牌检验 -- 认证成功返回用户信息
     */
    @Override
    public Result<UserVO> auth() {
        Integer userId = LocalThreadHolder.getUserId();
        User queryEntity = User.builder().id(userId).build();
        User user = userMapper.getByActive(queryEntity);
        UserVO userVO = new UserVO();
        BeanUtils.copyProperties(user, userVO);
        return ApiResult.success(userVO);
    }

    /**
     * 分页查询用户数据
     */
    @Override
    public Result<List<User>> query(UserQueryDto userQueryDto) {
        List<User> users = userMapper.query(userQueryDto);
        Integer count = userMapper.queryCount(userQueryDto);
        return PageResult.success(users, count);
    }

    /**
     * 用户信息修改
     */
    @Override
    public Result<String> update(UserUpdateDTO userUpdateDTO) {
        User updateEntity = User.builder().id(LocalThreadHolder.getUserId()).build();
        BeanUtils.copyProperties(userUpdateDTO, updateEntity);
        userMapper.update(updateEntity);
        return ApiResult.success();
    }

    /**
     * 批量删除用户信息
     */
    @Override
    public Result<String> batchDelete(List<Integer> ids) {
        if (ids == null || ids.isEmpty()) {
            return ApiResult.error("请选择要删除的用户");
        }
        Integer currentUserId = LocalThreadHolder.getUserId();
        if (ids.contains(currentUserId)) {
            return ApiResult.error("不能删除自己");
        }
        userMapper.batchDelete(ids);
        return ApiResult.success();
    }

    /**
     * 用户修改密码
     */
    @Override
    public Result<String> updatePwd(Map<String, String> map) {
        String oldPwd = map.get("oldPwd");
        String newPwd = map.get("newPwd");
        String againPwd = map.get("againPwd");
        if (Objects.isNull(oldPwd)) {
            return ApiResult.error("原始密码输入不能为空");
        }
        if (Objects.isNull(newPwd)) {
            return ApiResult.error("请输入新密码");
        }
        if (Objects.isNull(againPwd)) {
            return ApiResult.error("请补充确认密码");
        }
        if (!newPwd.equals(againPwd)) {
            return ApiResult.error("前后密码输入不一致");
        }
        User user = userMapper.getByActive(
                User.builder().id(LocalThreadHolder.getUserId()).build()
        );
        if (!passwordEncoder.matches(oldPwd, user.getUserPwd())) {
            return ApiResult.error("原始密码验证失败");
        }
        user.setUserPwd(passwordEncoder.encode(newPwd));
        userMapper.update(user);
        return ApiResult.success("密码修改成功");
    }

    /**
     * 通过ID查询用户信息（越权保护：读者只能查自己，管理员可查任意）
     */
    @Override
    public Result<UserVO> getById(Integer id) {
        Integer currentUserId = LocalThreadHolder.getUserId();
        Integer currentRole = LocalThreadHolder.getRoleId();
        boolean isAdmin = Objects.equals(currentRole, RoleEnum.ADMIN.getRole());
        if (!isAdmin && !Objects.equals(currentUserId, id)) {
            return ApiResult.error("无权查看其他用户信息");
        }
        User user = userMapper.getByActive(User.builder().id(id).build());
        if (user == null) {
            return ApiResult.error("用户不存在");
        }
        UserVO userVO = new UserVO();
        BeanUtils.copyProperties(user, userVO);
        return ApiResult.success(userVO);
    }

    /**
     * 后台新增用户
     */
    @Override
    public Result<String> insert(UserRegisterDTO userRegisterDTO) {
        User user = userMapper.getByActive(
                User.builder().userName(userRegisterDTO.getUserName()).build()
        );
        if (Objects.nonNull(user)) {
            return ApiResult.error("用户名已经被使用");
        }
        User entity = userMapper.getByActive(
                User.builder().userAccount(userRegisterDTO.getUserAccount()).build()
        );
        if (Objects.nonNull(entity)) {
            return ApiResult.error("账号不可用");
        }
        User saveEntity = User.builder()
                .userRole(RoleEnum.READER.getRole())
                .userName(userRegisterDTO.getUserName())
                .userAccount(userRegisterDTO.getUserAccount())
                .userAvatar(userRegisterDTO.getUserAvatar())
                .userPwd(passwordEncoder.encode(userRegisterDTO.getUserPwd()))
                .createTime(LocalDateTime.now())
                .isLogin(LoginStatusEnum.USE.getFlag()).build();
        userMapper.insert(saveEntity);
        return ApiResult.success("新增成功");
    }

    /**
     * 后台用户信息修改
     */
    @Override
    public Result<String> backUpdate(User user) {
        userMapper.update(user);
        return ApiResult.success();
    }

    /**
     * 统计指定时间里面的用户存量数据
     */
    @Override
    public Result<List<ChartVO>> daysQuery(Integer day) {
        QueryDto queryDto = DateUtil.startAndEndTime(day);
        UserQueryDto userQueryDto = new UserQueryDto();
        userQueryDto.setStartTime(queryDto.getStartTime());
        userQueryDto.setEndTime(queryDto.getEndTime());
        List<User> userList = userMapper.query(userQueryDto);
        List<LocalDateTime> localDateTimes = userList.stream().map(User::getCreateTime).collect(Collectors.toList());
        List<ChartVO> chartVOS = DateUtil.countDatesWithinRange(day, localDateTimes);
        return ApiResult.success(chartVOS);
    }

    /**
     * 冻结用户
     */
    @Override
    public Result<String> freezeUser(Integer userId) {
        userMapper.update(User.builder().id(userId).isLogin(true).build());
        return ApiResult.success("用户已冻结");
    }

    /**
     * 解冻用户
     */
    @Override
    public Result<String> unfreezeUser(Integer userId) {
        userMapper.update(User.builder().id(userId).isLogin(false).build());
        return ApiResult.success("用户已解冻");
    }
}
